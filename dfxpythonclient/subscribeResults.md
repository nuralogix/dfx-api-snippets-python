# subscribeResults

This class is an example that shows one way to receiving the results under one measurementID by creating a subscribe channel to the API server via Websockets.

*One may receive multiple results if one sends multiple data chunks. The intermediate results may have less result signals than the final result depends on the duration of each chunk and the number of chunks*

It depends upon the following packages:

```python
import asyncio # the Asynchronous io 
import os
from dfxpythonclient.measurement_pb2 import SubscribeResultsRequest # compiled version of the protobuf request to subscribe to the results
from google.protobuf.json_format import ParseDict # used to parse python dictionary to protobuf
import uuid # Used to generate uuid
import websockets # Websocket 
```
**Basic usage:**

Create the subscribeResults object with a measurementID, a token, a websocketHandler object, number of chunks, and an optional output folder.
```python
sub = subscribeResults(measurementID, token, websocketobj, num_chunks, out_folder=folder)
```
Add the `subscribe()` method to the event loop:
```python
loop = asyncio.get_event_loop()
loop.run_until_complete(sub.subscribe())
```

**Documentation:**

Let's examine the constructor of the Class. It requires a `measurementID` (the one you already have in addData and expecting result), a `token` issued by the DeepAffex server, a `websocketHandler` object, the total number of chunks `num_chunks` you sent to the server(so it knows when to disconnect) in use, and an optional output folder `out_folder` for writing the output files.
```python
def __init__(self, measurementID, token, websocketobj, num_chunks, out_folder=None):
    self.measurementID = measurementID
    self.token = token
    self.ws_url = websocketobj.ws_url
    self.num_chunks = num_chunks
    self.requestData = None
    self.ws_obj = websocketobj
    self.out_folder = out_folder

    if not out_folder:
        self.out_folder = "./receive"
    if not os.path.isdir(self.out_folder):  # Create directory if not there
        os.mkdir(self.out_folder)
```
Note that if no `out_folder` is specified at input, it would set a default folder to `"./receive"` inside the current local directory. If the specified output folder is nonexistent, it would create the folder.

It then calls the `prepare_data` method to prepare the request data that need to be sent through the websocket.
```python
def prepare_data(self):
    data = {}
    wsID = self.ws_obj.ws_ID		# Get websocket ID from the WebsocketHandler object
    requestID = uuid.uuid4().hex[:10]
    data['RequestID'] = requestID
    data['Query'] = {}
    data['Params'] = dict(ID=self.measurementID)

    websocketRouteID = '0510'
    requestMessageProto = ParseDict(
        data, SubscribeResultsRequest(), ignore_unknown_fields=True)
    self.requestData = f'{websocketRouteID:4}{wsID:10}'.encode(
    ) + requestMessageProto.SerializeToString()		# Data to be sent
```

As mentioned in the API documents, you will need to provide a unique `requestID` (for destinguishing between different websocket connections if you have), the `websocketRouteID` ('0510' for subscribeResult mentioned in the API ducumentation), and the measurementID as a dictionary to `'Params'`. It then uses the protobuf definition (compiled version) and the the `SerializeToString()` provided by google to create the data to be sent and put it into the websocket request data's `[10:]` buffer. The `[0:4]` is the unique websocket ID. 

In the `subscribe()` method, we prepare the data and call `handle_send`, aynchronously. This sends the prepared `requestData` prepared above through websocket asynchronously.
```python
await self.prepare_data()
await self.ws_obj.handle_send(self.requestData)
```

It then polls continuously until all the chunks have been received, indicated by a counter. It checks two stacks, `self.ws_obj.subscribeStats` for confirmation messages, and `self.ws_obj.chunks` for payload chunks, and handles each case differently.
```python
counter = 0
while counter < self.num_chunks:
    await self.ws_obj.handle_recieve()
    if self.ws_obj.subscribeStats:		# If a confirmation status is received
        response = self.ws_obj.subscribeStats[0]
        self.ws_obj.subscribeStats = []
        statusCode = response[10:13].decode('utf-8')
        if statusCode != '200':			# Error
            print("Status:", statusCode)

    elif self.ws_obj.chunks:			# If a chunk is received
        counter += 1
        response = self.ws_obj.chunks[0]
        self.ws_obj.chunks = []
        print("Data received; Chunk: "+str(counter) + "; Status: "+str(statusCode))
        with open(self.out_folder+'/result_'+str(counter)+'.bin', 'wb') as f:	# Save the data locally
            f.write(response[13:])
```
If a "connection established" confirmation is received in `self.ws_obj.subscribeStats` (usually the first response only), we can ignore it unless there is an error.

The actual result is the `[13:]` part and we can just save them into the `self.output_folder` specified so you can call SDK to decode later:
```python
print("Data received; Chunk: "+str(counter)+"; Status: "+str(statusCode))
with open(self.out_folder+'/result_'+str(counter)+'.bin', 'wb') as f:
    f.write(response[13:])
```

Finally, when all the chunks have been received, we close the websocket by calling
```python
await self.ws_obj.handle_close()
```
