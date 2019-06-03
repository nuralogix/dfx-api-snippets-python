import asyncio
import argparse
from dfxpythonclient.createMeasurement import createMeasurement
from dfxpythonclient.subscribeResults import subscribeResults
from dfxpythonclient.addData import addData
from dfxpythonclient.websocketHelper import WebsocketHandler

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

# Create object for handling websockets
websocketobj = WebsocketHandler(token, ws_url) 

# Create Measurement
createmeasurementObj = createMeasurement(studyID, token, rest_url)
measurementID = createmeasurementObj.create()

# Create addData Object which prepares the data need to be sent in the input_directory
adddataObj = addData(measurementID, token, rest_url, websocketobj, input_directory)
# Create subscribeResults Object which prepares the subscribe request
subscriberesultsObj = subscribeResults(
    measurementID, token, websocketobj, adddataObj.num_chunks)

loop.run_until_complete(websocketobj.connect_ws())    # Must first connect websocket

# Add tasks to event loop
tasks = []
a = loop.create_task(subscriberesultsObj.subscribe())   # Subscribe to results
tasks.append(a)
b = loop.create_task(adddataObj.sendWS())               # Add data using websockets
tasks.append(b)
#c = loop.create_task(adddataObj.sendAsync())           # Add data using REST 
#tasks.append(c)

wait_tasks = asyncio.wait(tasks)
loop.run_until_complete(wait_tasks)
loop.close()