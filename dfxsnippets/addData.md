# addData

This class can be used to add data chunks under a `measurementID`. All you need
is the `measurementID`, the token you received from the "register/login"
process, and the base URL of the DFX API REST service

This class needs the following packages:

```python
import asyncio          #python's asyncio
import base64           #base64 format of the payload encoding
import functools        #construct an async function
import json             #json utilities
import os               #join the path
import requests         #send http request
import time             #for synchronous
from glob import glob   #for gathering the payload files

from dfxsnippets.adddata_pb2 import DataRequest	 # proto object for addData request
from dfxsnippets.websocketHelper import WebsocketHandler  # for handling websockets activity
```

## Basic usage

Create the object:

```python
addD = addData(MeasurementID, token, server_url, websocketobj, input_directory)
```

Send the data synchronously

```python
addD.sendSync()
```

Or send the data asynchronously (So you can use asyncio to send, receive,
`subscribeResult`s concurrently)

```python
addD.sendAsync()
```

## Understanding the class

### Constructor

Let's examine the constructor of the class. It requires a `measurementID` (the
return value of `createMeasurement.create()`), a token issued by the DFX server,
the URL to the REST API, a `websocketHandler` object, and a input directory of
DFX-SDK generated payload files (together with meta and properties files) in use.

```python
def __init__(self, measurementID, token, server_url, websocketobj, input_directory):
    self.measurementID = measurementID
    self.token = token
    self.server_url = server_url
    self.input_directory = input_directory
    self.chunks = []
    self.ws_obj = websocketobj
    if websocketobj:
        self.conn_method = 'Websocket'
    else:
        self.conn_method = 'REST'
    self.prepare_data()
```

### `prepare_data`

`self.prepare_data()` prepares the data to be sent.

Notice that `self.conn_method` is determined by the value of `websocketobj`.
For using **REST** to add data, simply pass in `None` for `websocketobj`; and
to use **websockets** for add data, pass in a valid `WebsocketHandler` object
for `websocketobj` (more on this in `websocketHelper.md`).

As you can see, it prepares the data chunk by chunk (You can send multiple
chunks to one `measurementID`, you may get a partial result for each chunk and an
aggregate result of all chunks).

One thing to notice is that the payload file has to be encoded using Base64
so it can be put into a JSON request.

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

For each chunk, we add an `Action`, which tells the server what to do with it -
`'FIRST'` for the first chunk, `'LAST'` for the last chunk and `'CHUNK'`
for any in-the-middle chunks

So if you are sending only one chunk, you should put `'LAST::PROCESS'` since it
is the last chunk you will send.

If you are sending two chunks, the first one should be `'FIRST::PROCESS'` while
the second should be `'LAST::PROCESS'`.

If you have more the two chunks, the first one should be `'FIRST::PROCESS'`
while the last one should be `'LAST::PROCESS'`; any other chunks should be
`'CHUNKS::PROCESS'`

```python
if i == 0 and total_num_payload > 1:
    action = 'FIRST::PROCESS'
elif i == total_num_payload - 1:
    action = 'LAST::PROCESS'
else:
    action = 'CHUNK::PROCESS'
```

Now we build the body of the HTTP request using this information and append the
data to `self.chunks` which buffers all the data that needs to be sent.

*Note: The properties file may have different field names based on different
versions of the DFX SDK that produced it so you might need to change those
field names. For example, the `chunk_number` maybe `chunkNumber` etc.. the
naming differences are handled here:*

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

The data format of the body differs by the type of connection used. For *REST*,
the data can be represented as a Python dictionary:

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

data['Meta'] = json.dumps(meta)  # stringfied json
data["Payload"] = base64.b64encode(payload).decode('utf-8')  # decode binary payload to base64

self.chunks.append(data)
```

But for the *websocket* transport, the data must be a DataRequest protobuf object,
which is defined as follows:

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

After `self.chunks` has been filled with data chunk by chunk, the object is
ready to be used to send data to the server.

There are two ways of sending:

1. Sending the data synchronously i.e. blocking

    ```python
    addD.sendSync()
    ```

    This function constructs the URL, embeds the token and sends the data chunks
    one by one to the server.

    ```python
    def sendSync(self):
        url = self.server_url + "/measurements/"+self.measurementID+"/data"
        headers=dict(Authorization="Bearer {}".format(self.token))
        headers['Content-Type'] =  "application/json"
        for chunk in self.chunks:
            response = requests.post(url,json=chunk, headers=headers)
    ```

    Notice that `sendSync()` only works if `self.conn_method == 'REST'`.
    This is because websocket operations are all asynchronous.

2. Send the data asynchronously

    ```python
    addD.sendAsync()
    ```

    In this function, it does the similar sending process but asynchronously,
    as the definition of the function shows - `async def sendAsync(self)`.
    The process, however, differs between REST and websocket transport.

    For *REST*, the asyncio happens here:

    ```python
    requestFunction = functools.partial(requests.post,
        url=url, json=chunk, headers=headers)
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(None, requestFunction)
    response = await future
    ```

    We use the Python `functools` module to create a wrapper function around the
    `requests.post` so that it can be `await`ed. Then we get the current
    eventloop and run the wrapped function in it.

    For *websockets*, first get the 4-digit `actionID` from the DFX API documentation
    ('0506' for `DataRequest`), and the 10-digit `wsID` from the `WebsocketHandler`
    object. Then all the data and information is encoded into a binary buffer of
    format `Buffer( [ string:4 ][ string:10 ][ string/buffer ] )` to be sent by through
    the websocket.

    ```python
    content = f'{actionID:4}{wsID:10}'.encode() + chunk.SerializeToString()
    ```

    Call this to send the encoded content:

    ```python
    await self.ws_obj.handle_send(content)
    ```

    `await` is needed since this is an asynchronous method. Then, we wait to get a
    response from the websocket.

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

    It keeps polling until the stack `self.ws_obj.addDataStats` receives something,
    which is a websocket response for add data. Remember that websocket responses are
    in this format: `Buffer( [ string:10 ][ string:3 ][ string/buffer ] )`.
    The `status_code` is decoded as the middle 3 digits. If the code is not '200', then
    there is an error when adding data.

    The advantage of async sending is that when I/O is busy to send this data,
    the eventloop can switch context to another async function and try the I/O
    of that one.

    For example, instead of waiting the second chunk to be sent, the eventloop
    can actually check if there's any result coming back for the first chunk
    in the `subscribeResult` object, which will be covered in the description of
    the `subscribeResult` object.

*Note: The API won't process the next chunk if it is received within time
window between the start time of the last chunk and the duration of the last
chunk. For example, if the last chunk has a duration of 15 seconds, it is
not possible, in a real-time measurement, to receive a second chunk short
than that time. This is usually not a problem when you are sending real
payloads collected by the SDK because it won't produce a second chunk
before the first chunk got extracted. This is the reason for the `sleep`ing in
the code:*

Sync version:

```python
if "LAST" not in chunk['Action']:
    print("sleep for the chunk duration")
    time.sleep(chunk['Duration'])
```

Async version:

(Again, while perform this async sleeping the eventloop can switch context to
other async functions):

```python
if "LAST" not in chunk['Action']:
    print("sleep for the chunk duration")
    await asyncio.sleep(chunk['Duration'])
```

You can check the response of each chunk to see the status code.
