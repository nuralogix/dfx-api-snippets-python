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
                      "base REST url to the DFX API" \
                      "base Websocket url to the DFX API" \
                      "your directory above"
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
```

Then, we parse the command line to set up the `studyId`, `token`, `restUrl`,
`websocketUrl`, and input directory to the payload files.

```python
parser = argparse.ArgumentParser()

parser.add_argument("studyID", help="StudyID")
parser.add_argument("token", help="user or device token")
parser.add_argument("restUrl", help="DFX API REST url")
parser.add_argument("wsUrl", help="DFX API Websocket url")
parser.add_argument("payloadDir", help="Directory of payload files")

args = parser.parse_args()

studyID = args.studyID
token = args.token
rest_url = args.restUrl
ws_url = args.wsUrl
input_directory = args.payloadDir
```

Then, we create the eventloop which manages all the async tasks:

```python
loop = asyncio.get_event_loop()
```

Then, we create a Measurement and get it's `measurementID`

```python
createmeasurementObj = createMeasurement(studyID, token, rest_url)
measurementID = createmeasurementObj.create()
```

Then, we create an `addData` object which prepares the data need to be sent in
the `input_directory`

```python
adddataObj = addData(measurementID, token, rest_url, input_directory)
```

Then, we create a `subscribeResults` object which prepares the subscribeResults
request

```python
subscriberesultsObj = subscribeResults(measurementID, token, ws_url, adddataObj.num_chunks)
```

Then, we add the `subscribeResults.subscribe()` method to an `async` task list

```python
tasks = []
t = loop.create_task(subscriberesultsObj.subscribe())
tasks.append(t)
```

Then, we *start* the event loop by asking it to run until it finishes all the
chunks, sending requests in `addData.sendAsync()` asynchronously:

```python
loop.run_until_complete(adddataObj.sendAsync())
```

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
