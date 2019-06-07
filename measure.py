import argparse
import asyncio

from dfxsnippets.addData import addData
from dfxsnippets.createMeasurement import createMeasurement
from dfxsnippets.subscribeResults import subscribeResults
from dfxsnippets.websocketHelper import WebsocketHandler

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DFX API Python snippets example")

    parser.add_argument("studyID", help="StudyID")
    parser.add_argument("token", help="user or device token")
    parser.add_argument("payloadDir", help="Directory of payload files")
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

    args = parser.parse_args()

    studyID = args.studyID
    token = args.token
    rest_url = args.restUrl
    ws_url = args.wsUrl
    conn_method = args.connectionMethod
    input_directory = args.payloadDir
    output_directory = args.outputDir

    # Create the async event loop
    loop = asyncio.get_event_loop()

    # Create object for handling websockets
    websocketobj = WebsocketHandler(token, ws_url)

    # Create a measurement object and get a measurement ID
    createmeasurementObj = createMeasurement(studyID, token, rest_url)
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
