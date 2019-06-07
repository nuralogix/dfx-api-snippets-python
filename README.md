# DFX API Python Snippets

This repository contains snippets of Python code you may find useful to connect to the
NuraLogix DeepAffex API

## Getting started

* Create and activate your python3.6 environment and run `pip install .`
* Get payload files(payload, metadata, properties) from the DFX SDK and save
  them in a directory
* In a shell, run:

    ```bash
    python measure.py "studyID received from Nuralogix" \
                      "Token from registration/login process"
                      "your directory above" \
                      --restUrl="base REST url to the DFX API" \
                      --wsUrl="base Websocket url to the DFX API" \
                      --outputDir="directory for results" \
                      --connectionMethod="Websocket"
    ```

## Let's take a look at `measure.py`

First we import what we need:

```python
import asyncio  # For async operations
import argparse # For parsing arguments

# The followings are the libraries we made in the dfxsnippets directory
# Refer to each .md files of them for detailed description
from dfxsnippets.createMeasurement import createMeasurement
from dfxsnippets.subscribeResults import subscribeResults
from dfxsnippets.addData import addData
from dfxsnippets.websocketHelper import WebsocketHandler
```

Then, we parse the command line to set up the `studyId`, `token`, `restUrl`,
`websocketUrl`, the input directory to the payload files, output directory,
connection method (can only be "REST" or "Websocket"),

```python
parser = argparse.ArgumentParser()

parser.add_argument("studyID", help="StudyID")
parser.add_argument("token", help="user or device token")
parser.add_argument("payloadDir", help="Directory of payload files")
parser.add_argument("--restUrl", help="DFX API REST url", default="https://qa.api.deepaffex.ai:9443")
parser.add_argument("--wsUrl", help="DFX API Websocket url", default="wss://qa.api.deepaffex.ai:9080")
parser.add_argument("--outputDir", help="Directory for received files", default=None)
parser.add_argument("--connectionMethod", help="Connection method", choices=["REST", "Websocket"], default="REST")

args = parser.parse_args()

studyID = args.studyID
token = args.token
rest_url = args.restUrl
ws_url = args.wsUrl
conn_method = args.connectionMethod
input_directory = args.payloadDir
output_directory = args.outputDir
```

Then, we create the eventloop which manages all the async tasks:

```python
loop = asyncio.get_event_loop()
```

and a `WebsocketHandler` object for handling websockets:

```python
websocketobj = WebsocketHandler(token, ws_url)
```

We create a Measurement and get it's `measurementID`

```python
createmeasurementObj = createMeasurement(studyID, token, rest_url)
measurementID = createmeasurementObj.create()
```

Then, we create an `addData` object which prepares the data to be sent from
the `input_directory`. If the connection method is `'REST'` then pass in `None` for `websocketobj`.

```python
if conn_method == 'REST':
    adddataObj = addData(measurementID, token, rest_url, None, input_directory)
else:
    adddataObj = addData(measurementID, token, rest_url, websocketobj, input_directory)
```

Then, we create a `subscribeResults` object which prepares the `subscribeResults`
request

```python
subscriberesultsObj = subscribeResults(
    measurementID, token, websocketobj, adddataObj.num_chunks, out_folder=output_directory)
```

We connect to the websocket first in the event loop (if this is not done first
there will be errors). This starts the event loop.

```python
loop.run_until_complete(websocketobj.connect_ws())
```

Add the `adddataObj.sendAsync()` and `subscribeResults.subscribe()` method to an `async` task list:

```python
tasks = []
tasks.append(loop.create_task(adddataObj.sendAsync()))
tasks.append(loop.create_task(subscriberesultsObj.subscribe()))
```

Since the event loop has already been started when doing `websocketobj.connect_ws()`,
it will just run the remaining tasks in order asynchronously.

*In this process, whenever the `sendAsync`s are `await`ing for I/O operation to
finish, the event loop will try to switch context to the next async task that
is not `await`ing, which is the `subscribeResults.subscribe()` in our case.*

At this point, once the event loop has finished all the chunks in
`addData.sendAsync()`, we ask the eventloop to keep running until the
`subscribeResults.subscribe()` finishes, which will return when all chunks
results are received, in the task list to finish.

```python
wait_tasks = asyncio.wait(tasks)
loop.run_until_complete(wait_tasks)
loop.close()
```
