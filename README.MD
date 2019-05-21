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
```
It parses the input first and then set the studyId, token, rest Url, websocket Url, and input directory to the payloads files.
```python
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
```

create the eventloop which manages all the async tasks:
```python
loop = asyncio.get_event_loop()
```
create Measurement and get the measurementID
```python
createmeasurementObj = createMeasurement(studyID, token, rest_url)
measurementID = createmeasurementObj.create()
```
create addData Object which prepares the data need to be sent in the input_directory
```python
adddataObj = addData(measurementID, token, rest_url, input_directory)
```
create subscribeResults Object which prepares the subscribeResuls request
```python
subscriberesultsObj = subscribeResults(
    measurementID, token, ws_url, adddataObj.num_chunks)
```

Add the `subscribeResults.subscribe()` method to an `async` task list
```python
tasks = []
t = loop.create_task(subscriberesultsObj.subscribe())
tasks.append(t)
```
*Start* the event loop by ask it to run until it finish all the chunks' sending requests in `addData.sendAsync()` asynchronously:
```python
loop.run_until_complete(adddataObj.sendAsync())
```
*In the above process, whenever the `sendAsync` are `await`ing for IO operation to finish, the event loop will try to switch context to the next async task that is not `await`ing, which is the `subscribeResults.subscribe()` in our case.*

At this point, the event loop finished all the chunks in `addData.sendAsync()`, we ask the eventloop to keep running until the `subscribeResults.subscribe()`, which will return when all chunks results are received, in the task list to finish.
```python
wait_tasks = asyncio.wait(tasks)
loop.run_until_complete(wait_tasks)
loop.close()
```