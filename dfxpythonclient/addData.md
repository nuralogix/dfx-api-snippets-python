# addData
This class can be used to add data chunks under a measurement, given the measurement ID. All you need is the measurementID, the token you received from the "register/login" process, and the base url of the dfx api rest service.

This class needs the following packages:
```python
import functools        #construct an async function 
import asyncio          #python's asyncio
import base64           #base64 format of the payload encoding
import requests         #send http request
import json             #json utilities
import time             #for synchronous 
from glob import glob   #for gathering the payload files
import os               #join the path

from dfxpythonclient.adddata_pb2 import DataRequest		#proto object for addData request
from dfxpythonclient.websocketHelper import WebsocketHandler	#for handling websockets activity
```
**Basic usage:**

Create the object:
```python
addD = addData(MeasurementID, token, server_url, websocketobj, input_directory)
```
Send the data synchronously
```python
addD.sendSync()
```
Or send the data asynchronously(In this way you can use the asyncio to send and receive, subscribeResult, concurrently)

```python
addD.sendAsync()
```

**Documentation:**

Let's examine the constructor of the Class. It requires a `measurementID` (the return value of `createMeasurement.create()`), a `token` issued by the Deepaffex server, the `server_url` to the REST API, a `websocketHandler` object, and a `input_directory` of DFX-SDK generated payload files(together with meta and properties files) in use.

```python
def __init__(self, measurementID, token, server_url, websocketobj, input_directory):
```
Notice that `self.conn_method` is determined by the value of `websocketobj`. For using **REST** to add data, simply pass in `None` for `websocketobj`; and to use **websockets** for add data, pass in a valid `WebsocketHandler` object for `websocketobj` (more on this in `websocketHelper.md`).

It then calls the `self.prepare_data()` to prepare the data to be sent. 

As you can see, it prepares the data chunk by chunk (You can send multiple chunks to one measurementID, you may get partial result for each chunk and a total result of all chunks).

One thing to notice is that the payload file has to be decoded using `payload = base64.b64encode(fileContent).decode('utf-8')` so it can be put in json.
```python
for i in range(total_num_payload):
    with open(os.path.join(self.input_directory,'payload'+ str(i) + '.bin'), 'rb') as input_file:
        fileContent = input_file.read()
    payload = fileContent
    with open(os.path.join(self.input_directory,'metadata'+ str(i) + '.bin'), 'r') as input_file:
        meta = json.load(input_file)
    with open(os.path.join(self.input_directory,'properties'+ str(i) + '.json'), 'r') as input_file:
        properties = json.load(input_file)
```
For each chunk, we add `action`, which tells the server what to do with each chunk. The 'FIRST' tells it is the first chunk; the 'LAST' tells it is the last chunk; the 'CHUNK' tells it is a in-the-middle chunk

So if you are sending only 1 chunk, you should put `'LAST::PROCEESS'` since it is the last chunk you will send.

If you are sending two chunks, the first one should be `'FIRST::PROCESS'` while the second should be `'LAST::PROCESS'`.

If you have more the two chunks, the first one should be `'FIRST::PROCESS'` while the second should be `'LAST::PROCESS'`, any other chunks should be `'CHUNKS::PROCESS'`

```python
    if i == 0 and total_num_payload > 1:
        action = 'FIRST::PROCESS'
    elif i == total_num_payload - 1:
        action = 'LAST::PROCESS'
    else:
        action = 'CHUNK::PROCESS'
```
For the properties, since older DFX SDK versions have different names (for example, 'chunkNumber' vs. 'chunk_number'), the naming differences are handled here: 
```python
    if (meta["dfxsdk"] < "4.0"):
        chunkOrder = properties['chunkNumber']
        startTime = properties['startTime_s']
        endTime = properties['endTime_s']
    else:
        chunkOrder = properties['chunk_number']
        startTime = properties['start_time_s']
        endTime = properties['end_time_s']
    duration = properties['duration_s']
```
Then it fills the body part of the http request using these information and append the data to `self.chunks` which buffers all the data that needs to be sent. The data format differs by the type of connection used. For **REST**, the data can be represented as a Python dictionary:
```python
    data = {}
    data["ChunkOrder"] = chunkOrder
    data["Action"]     = action
    data["StartTime"]  = startTime
    data["EndTime"]    = endTime
    data["Duration"]   = duration
    # Additional meta fields !
    meta['Order'] = chunkOrder
    meta['StartTime'] = startTime
    meta['EndTime'] = endTime
    meta['Duration'] = data['Duration']

    data['Meta'] = json.dumps(meta)									#stringfied json
    data["Payload"] = base64.b64encode(payload).decode('utf-8')		#decode binary payload to base64

    self.chunks.append(data)
```
But for **websocket** transport, the data must be a DataRequest proto object, which is defined as follows:
```python
    data = DataRequest()
    paramval = data.Params
    paramval.ID = self.measurementID

    data.ChunkOrder = chunkOrder
    data.Action     = action
    data.StartTime  = startTime
    data.EndTime    = endTime
    data.Duration   = duration
    # Additional meta fields !
    meta['Order'] = chunkOrder
    meta['StartTime'] = startTime
    meta['EndTime'] = endTime
    meta['Duration'] = data.Duration

    data.Meta = json.dumps(meta).encode()	#encode stringfied json to bytes 
    data.Payload = bytes(payload)		#encode binary payload to bytes

```

After the `self.chunks` got filled with data chunk by chunk, the object is ready to be used to send data to the server.

There are two ways of sending:

1. Send the data synchronously
    ```python
        addD.sendSync()
    ```
    In this function, it constuct the url and embeds the token and send the data chunks one by one to the server
    ```python
        url = self.server_url + "/measurements/"+self.measurementID+"/data"
        headers=dict(Authorization="Bearer {}".format(self.token))
        headers['Content-Type'] =  "application/json"
        for chunk in self.chunks:
            response = requests.post(url,json=chunk, headers=headers)
    ```
    Notice that `sendSync()` only works if `self.conn_method == 'REST'`. This is because websocket operations are all asynchronous. 

2. Send the data asynchronously
    ```python
    addD.sendAsync()
    ```
    In this function, it does the similar sending process but asynchronously, as the definition of the function shows:
    `async def sendAsync(self)`. The process, however, differs between REST and websocket transport. 

    For *REST*, the asyncio happens here:
    ```python 
        requestFunction = functools.partial(requests.post,
            url=url, json=chunk, headers=headers)
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(None, requestFunction)
        response = await future
    ```
    We use the python functools to create a wrapper function around the `requests.post` so that it can be `await`ed. Then we get the current eventloop and run the wrapped function in it.

	For *websockets*, first get the 4-digit `actionID` from the DFX API documentation ('0506' for `DataRequest`), and the 10-digit `wsID` from the `WebsocketHandler` object. Then all the data and information is encoded into a binary buffer of format `Buffer( [ string:4 ][ string:10 ][ string/buffer ] )` to be sent by through the websocket. 
    ```python
        content = f'{actionID:4}{wsID:10}'.encode() + chunk.SerializeToString()
    ```
    Call this to send the encoded content:
    ```python
        await self.ws_obj.handle_send(content)
    ```
    
    `await` is needed since this is an asynchronous method. Then, we wait to get a response from the websocket. 
    ```python
        while True:
            try:
                await asyncio.wait_for(self.ws_obj.handle_recieve(), timeout=10)
            except TimeoutError:
                break
            if self.ws_obj.addDataStats:
                response = self.ws_obj.addDataStats[0]
                self.ws_obj.addDataStats = []
                break
        status_code = response[10:13].decode('utf-8')
    ```
    It keeps polling until the stack `self.ws_obj.addDataStats` receives something, which is a websocket response for add data. Remember that websocket responses are in this format: `Buffer( [ string:10 ][ string:3 ][ string/buffer ] )`. The `status_code` is decoded as the middle 3 digits. If the code is not '200', then there is an error when adding data. 

    The advantage of this async sending is: When the IO is busy to send this data, the eventloop can switch context to another async function and try the IO of that one. For example: instead of waiting the second data to be sent, the eventloop can actually check if there's any result coming back from the first chunk in the subscribeResult object, which will be covered in the description of the subscribeResult object.

*One important thing is: the API won't process the next chunk if it is received within time window between the start time of the last chunk and the duration of the last chunk. For example, if the last chunk has a duration of 15 seconds, it is not possible, in a real-time measurement, to receive a second chunk short than that time.*

*You will not need this when you are sending real payloads collocted by the SDK because it won't produce a second chunk before the first chunk got extracted*

This is the reason for the sleeping in the code:
Sync version:
```python
if "LAST" not in chunk['Action']:
    print("sleep for the chunk duration")
    time.sleep(chunk['Duration'])
```
Async version ( Again, while perform this Async sleeping the eventloop can switch context to other async io function):
```python
if "LAST" not in chunk['Action']:
    print("sleep for the chunk duration")
    await asyncio.sleep(chunk['Duration'])
```

You can check the response of each chunk to see the status code.
