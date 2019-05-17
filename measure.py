import asyncio
import argparse
from dfxpythonclient.createMeasurement import createMeasurement
from dfxpythonclient.subscribeResults import subscribeResults
from dfxpythonclient.addData import addData

parser = argparse.ArgumentParser()

parser.add_argument("--studyID", help="StudyID")
parser.add_argument("--token", help="user or device token")
parser.add_argument("--restUrl", help="DFX Rest API base url")
parser.add_argument("--wsUrl", help="DFX Websocket base url")
parser.add_argument("--inputDir", help="DFX Websocket base url")

args = parser.parse_args()
print(args)

studyID = args.studyID
token = args.token
rest_url = args.restUrl
ws_url = args.wsUrl
input_directory = args.inputDir

loop = asyncio.get_event_loop()

#create Measurement
createmeasurementObj = createMeasurement(studyID,token, rest_url)
measurementID = createmeasurementObj.create()

# create addData Object which prepares the data need to be sent in the input_directory
adddataObj =  addData(measurementID, token, rest_url,input_directory)
# create subscribeResults Object which prepares the subscribe request
subscriberesultsObj = subscribeResults(measurementID, token, ws_url, adddataObj.num_chunks)

# Add
tasks=[]
t = loop.create_task(subscriberesultsObj.subscribe())
tasks.append(t)

loop.run_until_complete(adddataObj.sendAsync())

wait_tasks = asyncio.wait(tasks)
loop.run_until_complete(wait_tasks)
loop.close()

