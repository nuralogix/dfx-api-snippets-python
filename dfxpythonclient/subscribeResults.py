import asyncio
from dfxpythonclient.measurement_pb2 import SubscribeResultsRequest
import uuid
from google.protobuf.json_format import ParseDict
import websockets


class subscribeResults():
    def __init__(self, measurementID, token, ws_url, num_chunks):
        self.measurementID = measurementID
        self.token = token
        self.ws_url = ws_url
        self.num_chunks = num_chunks
        self.requestData = None

        self.prepare_data()

    def prepare_data(self):
        requestID = uuid.uuid4().hex[:10]
        data = {}
        data['RequestID'] = requestID
        data['Query'] = {}
        data['Params'] = dict(ID=self.measurementID)

        wsID = uuid.uuid4().hex[:10]  # Make this ID sequential or variable
        websocketRouteID = '510'
        requestMessageProto = ParseDict(
            data, SubscribeResultsRequest(), ignore_unknown_fields=True)
        self.requestData = f'{websocketRouteID:4}{wsID:10}'.encode(
        ) + requestMessageProto.SerializeToString()

    async def subscribe(self):
        headers = dict(Authorization="Bearer {}".format(self.token))
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
                    print("Data received; Chunk: "+str(counter) +
                          "; Status: "+str(statusCode))
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
