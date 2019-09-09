import argparse
import asyncio
import requests
import json
import datetime
import xlsxwriter as xls
import openpyxl as op
import pandas as pd
from os import path
from NamedAtomicLock import NamedAtomicLock

from dfxsnippets.addData import addData
from dfxsnippets.createMeasurement import createMeasurement
from dfxsnippets.subscribeResults import subscribeResults
from dfxsnippets.websocketHelper import WebsocketHandler

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DFX API Python snippets example")

    parser.add_argument("--studyID", help="StudyID")
    parser.add_argument("--licenseKey", help="License Key")
    parser.add_argument("--username", help="UserName")
    parser.add_argument("--password", help="Password")
    parser.add_argument("--payloadDir", help="Directory of payload files")
    parser.add_argument("--server",
                    help="Name of server to use",
                    choices=["qa", "dev", "prod", "prod-cn"],
                    default="dev")
    parser.add_argument("--outputDir", help="Directory for received files", default=None)
    parser.add_argument("--connectionMethod",
                        help="Connection method",
                        choices=["REST", "Websocket"],
                        default="REST")
    parser.add_argument("--mode", help="Measurement mode", default="DISCRETE")

    args = parser.parse_args()

    studyID = args.studyID
    license_key = args.licenseKey
    username = args.username
    password = args.password
    conn_method = args.connectionMethod
    input_directory = args.payloadDir
    output_directory = args.outputDir
    mode = args.mode
    server = args.server

    # INTERNAL: Get server urls given the server name
    if server == "qa":
        rest_url = "https://qa.api.deepaffex.ai:9443"
        ws_url = "wss://qa.api.deepaffex.ai:9080"
    elif server == "dev":
        rest_url = "https://dev.api.deepaffex.ai:9443"
        ws_url = "wss://dev.api.deepaffex.ai:9080"
    elif server == "prod":
        rest_url = "https://api.deepaffex.ai:9443"
        ws_url = "wss://api.deepaffex.ai:9080"
    elif server == "prod-cn":
        rest_url = "https://api.deepaffex.cn:9443"
        ws_url = "wss://api.deepaffex.cn:9080"

    # Register License and get device token
    data = {
            "Key": "{}".format(license_key),
            "DeviceTypeID": "DARWIN",
            "Name": "dfx-api-python-client",
            "Identifier": "api-test",
            "Version": "1.0"
            }
    headers = {"Content-Type": "application/json"}
    response = requests.post(rest_url+'/organizations/licenses', data=json.dumps(data), headers=headers)
    index1 = response.text.find('Token')
    index2 = response.text.find('\",\"UserID')
    deviceToken = response.text[index1+8:index2]
    print("Device Token: ", deviceToken)

    # Login and get user token
    userdata = {
                "Email": "{}".format(username),
                "Password": "{}".format(password)
                }
    userHeaders = {"Content-Type": "application/json", "Authorization": "{}".format(deviceToken)}
    userResposne = requests.post(rest_url+'/users/auth', data=json.dumps(userdata), headers=userHeaders)
    userToken = userResposne.text[10:-2]
    print("User Token: ", userToken)

    token = userToken

    # Create the async event loop and list of tasks
    loop = asyncio.get_event_loop()
    tasks = []

    # Create object for handling websockets
    websocketobj = WebsocketHandler(token, ws_url)

    # Establish websocket connection (must be done at the start)
    # Note: Will time out in 10 seconds if connection is not established
    tasks.append(loop.create_task(websocketobj.connect_ws()))
    wait_tasks = asyncio.wait(tasks, timeout=10)
    loop.run_until_complete(wait_tasks)

    # Create a measurement object and get a measurement ID
    createmeasurementObj = createMeasurement(studyID, token, rest_url, mode)
    # measurementID = createmeasurementObj.create()
    createMeaResults = createmeasurementObj.create()
    cretaeMeaTime = createMeaResults[0]
    measurementID = createMeaResults[1]

    # Create an addData object (which prepares the data need to be sent in the input_directory)
    if conn_method == 'REST':
        adddataObj = addData(measurementID, token, rest_url, None, input_directory)
    else:
        adddataObj = addData(measurementID, token, rest_url, websocketobj,
                             input_directory)

    # Create subscribeResults Object which prepares the subscribe request
    subscriberesultsObj = subscribeResults(measurementID,
                                           token,
                                           websocketobj,
                                           adddataObj.num_chunks,
                                           out_folder=output_directory)

    # Add tasks to event loop
    tasks.append(loop.create_task(adddataObj.sendAsync()))
    tasks.append(loop.create_task(subscriberesultsObj.subscribe()))

    # Run add data and subscribe to results
    wait_tasks = asyncio.wait(tasks)

    loop.run_until_complete(wait_tasks)

    # Retrieve measurement results
    meaHeaders = {"Content-Type": "application/json", "Authorization": "{}".format(userToken)}
    meaResponse = requests.get(rest_url+'/measurements/'+measurementID, headers=meaHeaders)
    print('*'*50)
    print("Measurement (", measurementID, ") Retrieve Results: \n", meaResponse.json())

    loop.close()

    # Calculate the total process time for each measurement
    subscribeResultsTime = subscriberesultsObj.subscribeResultsTime
    t1 = datetime.datetime.combine(datetime.date.today(), cretaeMeaTime)
    t2 = datetime.datetime.combine(datetime.date.today(), subscribeResultsTime)
    tDiff = t2 - t1
    print('*'*50)
    print("Measurement (", measurementID, ") Process Time(s): ", tDiff.total_seconds())
    print('*'*50)

    # Generate Test Report
    myLock = NamedAtomicLock('saveTimeToXL')
    if myLock.acquire(timeout=15):
        if path.exists('Test_Report.xlsx') == True:
            print("Test_Report.xlsx already exists, append to it.")

            df = pd.read_excel('Test_Report.xlsx')

            excelRow = [(measurementID, str(cretaeMeaTime), str(subscribeResultsTime), str(tDiff.total_seconds()))]
            df_new = pd.DataFrame(excelRow, columns=['Measurement ID', 'Create Measurement Time', 'Subscribe Measurement Time', 'Total Measurement Process Time'])
            # print("df_new: ", df_new)

            df = df.append(df_new, ignore_index=True)

            # print("df after append: ", df)
        
        else:
            print("Test_Report.xlsx does not exist, create a new one.")    

            excelRow = [(measurementID, str(cretaeMeaTime), str(subscribeResultsTime), str(tDiff.total_seconds()))]
            df = pd.DataFrame(excelRow, columns=['Measurement ID', 'Create Measurement Time', 'Subscribe Measurement Time', 'Total Measurement Process Time'])    

            # print("df after create: ", df)

        df.to_excel('Test_Report.xlsx', index=False)

        print('Measurement: '+measurementID+' has been saved to Test Report!')

        myLock.release()
    else:
        print('*****!!!!! Unable to acquire lock !!!!!!*****')