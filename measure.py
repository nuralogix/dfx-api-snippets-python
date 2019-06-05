import asyncio
import argparse
from dfxpythonclient.createMeasurement import createMeasurement
from dfxpythonclient.subscribeResults import subscribeResults
from dfxpythonclient.addData import addData
from dfxpythonclient.websocketHelper import WebsocketHandler


parser = argparse.ArgumentParser()
parser.add_argument("--studyID", help="StudyID")
parser.add_argument("--token", help="user or device token")
parser.add_argument("--payloadDir", help="Directory of payload files")
parser.add_argument("--outputDir", help="Directory for received files", default="./receive")
parser.add_argument("--connectionMethod", choices=["REST", "Websocket"], help="Connection method")
parser.add_argument("--restUrl", help="DFX API REST url", default="https://qa.api.deepaffex.ai:9443")
parser.add_argument("--wsUrl", help="DFX API Websocket url", default="wss://qa.api.deepaffex.ai:9080")

args = parser.parse_args()
print(args)

studyID = args.studyID
token = args.token
rest_url = args.restUrl
ws_url = args.wsUrl
conn_method = args.connectionMethod
input_directory = args.payloadDir
output_directory = args.outputDir

loop = asyncio.get_event_loop()

# Create object for handling websockets
websocketobj = WebsocketHandler(token, ws_url) 

# Create Measurement
createmeasurementObj = createMeasurement(studyID, token, rest_url)
measurementID = createmeasurementObj.create()

# Create addData Object which prepares the data need to be sent in the input_directory
if conn_method == 'REST':
    adddataObj = addData(measurementID, token, rest_url, None, input_directory)
else:
    adddataObj = addData(measurementID, token, rest_url, websocketobj, input_directory)

# Create subscribeResults Object which prepares the subscribe request
subscriberesultsObj = subscribeResults(
    measurementID, token, websocketobj, adddataObj.num_chunks, out_folder=output_directory)

loop.run_until_complete(websocketobj.connect_ws())    # Must first connect websocket

# Add tasks to event loop
# In one thread, can only make one addData and one subscribeResults call at a time
tasks = []
b = loop.create_task(adddataObj.sendAsync())           # Add data
tasks.append(b)
a = loop.create_task(subscriberesultsObj.subscribe())   # Subscribe to results
tasks.append(a)

wait_tasks = asyncio.wait(tasks)
loop.run_until_complete(wait_tasks)
loop.close()