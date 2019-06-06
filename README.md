# How to use

1. Create and activate your python3.6 environment and run `pip install .`
2. Get payloads files(payload, metadata, properties) from the SDK and save them in a directory
3. Run `python measure.py --inputDir="your directory above" --restUrl=="base REST url to the dfx api" --wsUrl=="base Websocket url to the dfx api" --studyID="studyID received from Nuralogix" --token="Token you get from the registration/login process to the dfx api" `

# The measure.py

It needs the following packages:
```python
import asyncio  # asyncio from python
import argparse # parse the arguments
# The followings are the libraries we made in the dfxpythonclient directory
# Refer to each .md files of them for detailed description
from dfxpythonclient.createMeasurement import createMeasurement
from dfxpythonclient.subscribeResults import subscribeResults
from dfxpythonclient.addData import addData
from dfxpythonclient.websocketHelper import WebsocketHandler
```
It parses the input first and then set the studyId, token, payload directory, output directory, connection method (can only be "REST" or "Websocket"), rest Url and websocket Url. The arguments with default values are optional.
```python
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
```

Create the asyncio eventloop which manages all the async tasks:
```python
loop = asyncio.get_event_loop()
```

Create `WebsocketHandler` object for handling websockets:
```python
websocketobj = WebsocketHandler(token, ws_url) 
```

Create Measurement and get the `measurementID`:
```python
createmeasurementObj = createMeasurement(studyID, token, rest_url)
measurementID = createmeasurementObj.create()
```

Create `addData` object which prepares the data need to be sent in the input_directory. If the connection method is `'REST'` then pass in `None` for `websocketobj`.
```python
if conn_method == 'REST':
    adddataObj = addData(measurementID, token, rest_url, None, input_directory)
else:
    adddataObj = addData(measurementID, token, rest_url, websocketobj, input_directory)
```

Create `subscribeResults` object which prepares the subscribe to results request:
```python
subscriberesultsObj = subscribeResults(
    measurementID, token, websocketobj, adddataObj.num_chunks, out_folder=output_directory)
```

Connect the websocket first in the event loop (if this is not done first there will be errors). This starts the event loop.
```python
loop.run_until_complete(websocketobj.connect_ws())
```

Add the `adddataObj.sendAsync()` and `subscribeResults.subscribe()` method to an `async` task list:
```python
tasks = []
a = loop.create_task(adddataObj.sendAsync())           # Add data
tasks.append(a)
b = loop.create_task(subscriberesultsObj.subscribe())   # Subscribe to results
tasks.append(b)

```
Since the event loop has already been started when doing `websocketobj.connect_ws()`, it will just run the remaining tasks in order asynchronously. 

*In the above process, whenever the `sendAsync` are `await`ing for IO operation to finish, the event loop will try to switch context to the next async task that is not `await`ing, which is the `subscribeResults.subscribe()` in our case.*

At this point, the event loop finished all the chunks in `addData.sendAsync()`, we ask the eventloop to keep running until the `subscribeResults.subscribe()`, which will return when all chunks results are received, in the task list to finish.
```python
wait_tasks = asyncio.wait(tasks)
loop.run_until_complete(wait_tasks)
loop.close()
```
