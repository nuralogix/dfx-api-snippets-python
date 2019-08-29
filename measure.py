import argparse
import asyncio
import requests
import json

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
    parser.add_argument("--restUrl",
                        help="DFX API REST url",
                        default="https://qa.api.deepaffex.ai:9443")
    parser.add_argument("--wsUrl",
                        help="DFX API Websocket url",
                        default="wss://qa.api.deepaffex.ai:9080")
    parser.add_argument("--outputDir", help="Directory for received files", default=None)
    parser.add_argument("--connectionMethod",
                        help="Connection method",
                        choices=["REST", "Websocket"],
                        default="REST")
    parser.add_argument("--mode", help="Mode", default="DISCRETE")

    args = parser.parse_args()

    studyID = args.studyID
    license_key = args.licenseKey
    username = args.username
    password = args.password
    rest_url = args.restUrl
    ws_url = args.wsUrl
    conn_method = args.connectionMethod
    input_directory = args.payloadDir
    output_directory = args.outputDir
    mode = args.mode

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
    userheaders = {"Content-Type": "application/json", "Authorization": "{}".format(deviceToken)}
    userResposne = requests.post(rest_url+'/users/auth', data=json.dumps(userdata), headers=userheaders)
    userToken = userResposne.text[10:-2]
    print("User Token: ", userToken)

    token = userToken

    # Create the async event loop
    loop = asyncio.get_event_loop()

    # Create object for handling websockets
    websocketobj = WebsocketHandler(token, ws_url)

    # Create a measurement object and get a measurement ID
    createmeasurementObj = createMeasurement(studyID, token, rest_url, mode)
    measurementID = createmeasurementObj.create()

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

    # Must first connect websocket
    loop.run_until_complete(websocketobj.connect_ws())

    # Add tasks to event loop
    tasks = []
    tasks.append(loop.create_task(adddataObj.sendAsync()))
    tasks.append(loop.create_task(subscriberesultsObj.subscribe()))

    wait_tasks = asyncio.wait(tasks) 
    loop.run_until_complete(wait_tasks)
    loop.close()
