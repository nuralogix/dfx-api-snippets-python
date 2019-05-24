# subscribeResults

This class shows one way of receiving the results for a `measurementID` by
creating a subscribed channel to the DFX API server via WebSockets.

It depends upon the following packages:

```python
import asyncio # the Asynchronous io
from dfxpythonclient.measurement_pb2 import SubscribeResultsRequest # compiled version of the protobuf request to subscribe to the results
import uuid # Used to generate uuid
from google.protobuf.json_format import ParseDict # used to parse python dictionary to protobuf
import websockets # Websocket
```

## Basic usage

Create the `subscribeResults` object with a `measurementID`, a token and a
WebSocket URL to the DFX API server.

```python
sub = subscribeResults(measurementID, token, ws_url, num_chunks)
```

Add the `sub()` method to the event loop:

```python
loop = asyncio.get_event_loop()
loop.run_until_complete(sub.subscribe())
```

*Note: You may receive multiple results if you sends multiple data chunks.
The intermediate results may have fewer result signals than the final result
depends on the duration of each chunk and the number of chunks*

## Understanding the class

### Constructor

Let's examine the constructor. It requires a `measurementID` (the one you
already `addData`ed for and are expecting results), a token issued by the
DeepAffex server, the URL to the WebSocket address, and the total number of
chunks you sent to the server (so it knows when to disconnect.)

```python
def __init__(self, measurementID, token, ws_url, num_chunks)
```

### `prepare_data`

The `prepare_data` method is used to prepare the request data that need to
be sent through the WebSocket.

```python
def prepare_data(self):
    requestID=uuid.uuid4().hex[:10]
    data = {}
    data['RequestID'] = requestID
    data['Query'] = {}
    data['Params'] = dict(ID=self.measurementID)

    wsID = uuid.uuid4().hex[:10] # Make this ID sequential or variable
    websocketRouteID = '510'
    requestMessageProto = ParseDict(data, SubscribeResultsRequest(), ignore_unknown_fields=True)
    self.requestData = f'{websocketRouteID:4}{wsID:10}'.encode() + requestMessageProto.SerializeToString()
```

As mentioned in the DFX API documentation, you will need to provide a unique
`requestID` (for destinguishing between different WebSocket connections you
have), the `websocketRouteID` (*510* for `subscribeResult` mentioned in the API
documentation), and the `measurementID` as a dictionary to `'Params'`.

It then uses the protobuf definition (compiled version) and the `SerializeToString()`
provided by protobuf to create the data to be sent and put it into the WebSocket
request data's `[10:]` buffer. The `[0:4]` is the unique WebSocket ID.

### `sub`

In the `sub()` method, we use the token and the URL to create a WebSocket
connection, aynchronously.

```python
headers=dict(Authorization="Bearer {}".format(self.token))
websocket = await websockets.client.connect(self.ws_url, extra_headers=headers)
```
It then send the `requestData` prepared above to the WebSocket asynchronously.

```python
await websocket.send(self.requestData)
```

It then asynchronously waits for response data incoming via that WebSocket (it
will time out if nothing is received in 40 seconds) in a `while` loop:

```python
response = await asyncio.wait_for(websocket.recv(), timeout=40)
```

The first response is a "connection established" ack, we can ignore it.

The unique WebSocket id and status code can be extracted in the response in
those certain bytes

```python
_id = response[0:10].decode('utf-8')
statusCode = response[10:13].decode('utf-8')
```

The actual result are in the `[13:]` part and we just save them into the disk
so you can call SDK to decode them later:

```python
print("Data received; Chunk: "+str(counter)+"; Status: "+str(statusCode))
with open('./result_'+str(counter)+'.bin', 'wb') as f:
    f.write(response[13:])
```

It then increments the counter and when we have received all the chunks results,
it breaks the `while` loop and closes the WebSocket:

```python
counter += 1
if counter > self.num_chunks:
    print(" Closing websocket ")
    await websocket.close()
    break
```
