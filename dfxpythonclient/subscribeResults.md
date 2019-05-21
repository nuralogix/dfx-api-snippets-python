```python
import asyncio
from dfxpythonclient.measurement_pb2 import SubscribeResultsRequest
import uuid
from google.protobuf.json_format import ParseDict
import websockets

class subscribeResults():
    def __init__(self, measurementID, token, ws_url,num_chunks):
        self.measurementID = measurementID
        self.token = token
        self.ws_url = ws_url
        self.num_chunks = num_chunks
        self.requestData = None

        self.prepare_data()

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

    async def subscribe(self):
        headers=dict(Authorization="Bearer {}".format(self.token))
        websocket = await websockets.client.connect(self.ws_url, extra_headers=headers)
        await websocket.send(self.requestData)
        counter = 0
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=40)
            except asyncio.TimeoutError:
                response = ""
                await websocket.close()
                return
            if response:
                _id = response[0:10].decode('utf-8')
                statusCode = response[10:13].decode('utf-8')
                if counter == 0:
                    print("Status:", statusCode)
                    print("websocket connected")
                else:
                    print("Data received; Chunk: "+str(counter)+"; Status: "+str(statusCode))
                    with open('./result_'+str(counter)+'.bin', 'wb') as f:
                        f.write(response[13:])
            counter += 1
            if counter > self.num_chunks:
                    print(" Closing websocket ")
                    await websocket.close()
                    break

if __name__ == '__main__':
    measurementID = ''
    token = ''
    ws_url = ''
    num_chunks = 2
    sub = subscribeResults(measurementID, token, ws_url, num_chunks)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sub.subscribe())

```
# subscribeResults

This class is an example that shows one way to receiving the results under one measurementID by creating a subscribe channel to the API server via Websockets.

*One may receive multiple results if one sends multiple data chunks. The intermediate results may have less result signals than the final result depends on the duration of each chunk and the number of chunks*

It depends upon the following packages:

```python
import asyncio # the Asynchronous io 
from dfxpythonclient.measurement_pb2 import SubscribeResultsRequest # compiled version of the protobuf request to subscribe to the results
import uuid # Used to generate uuid
from google.protobuf.json_format import ParseDict # used to parse python dictionary to protobuf
import websockets # Websocket 
```
Basic usage:
Create the subscribeResults object with a measurementID, a token and a websocket url to the dfx api server.
```python
sub = subscribeResults(measurementID, token, ws_url, num_chunks)
```
Add the `sub()` method to the event loop:
```python
loop = asyncio.get_event_loop()
loop.run_until_complete(sub.subscribe())
```
Let's examine the constructor of the Class. It requires a measurementID(the one you already addData and expecting result), a token issued by the Deepaffex server, the url to the Websocket address, and the total number of chunks you sent to the server(so it knows when to disconnect) in use.
```python
def __init__(self, measurementID, token, ws_url,num_chunks)
```
It then call the `prepare_data` method to prepare the request data that need to be sent through the websocket.
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
As mentioned in the API documents, you will need to provide a unique requestID(for destinguishing between different websocket connections if you have), the websocketRouteID (*510* for subscribeResult mentioned in the API ducumentation), and the measurementID as a dictionary to `'Params'`. It then use the protobuf definition(compiled version) and the the `SerializeToString()` provided by google to create the data to be sent and put it into the websocket request data's `[10:]` buffer. The `[0:4]` is the unique websocket ID. 

In the `sub()` method, we use the token and the url to create a websocket connection, aynchronously.
```python
headers=dict(Authorization="Bearer {}".format(self.token))
websocket = await websockets.client.connect(self.ws_url, extra_headers=headers)
```
It then send the `requestData` prepared above through websocket asynchronously.
```python
await websocket.send(self.requestData)
```
It then asynchronously wait for response data incoming via that websocket( it will time out if nothing is received in 40 seconds) in a `while` loop:
```python
response = await asyncio.wait_for(websocket.recv(), timeout=40)
```
The first response is a "connection established" ack, we can ignore it.

The uniqe websocket id and status code can be extracted in the response in those certain bytes
```python
_id = response[0:10].decode('utf-8')
statusCode = response[10:13].decode('utf-8')
```
The actual result are `[13:]` part and we just save them into the disk so you can call SDK to decode later:
```python
print("Data received; Chunk: "+str(counter)+"; Status: "+str(statusCode))
with open('./result_'+str(counter)+'.bin', 'wb') as f:
    f.write(response[13:])
```
It then ++ the counter and when we received all the chunks results, it breaks the `while` loop and close the websocket:
```python
counter += 1
if counter > self.num_chunks:
    print(" Closing websocket ")
    await websocket.close()
    break
```