import asyncio
from dfxpythonclient.measurement_pb2 import SubscribeResultsRequest
import uuid
from google.protobuf.json_format import ParseDict
import websockets


class subscribeResults():
    def __init__(self, measurementID, token, websocketobj, num_chunks):
        self.measurementID = measurementID
        self.token = token
        self.ws_url = websocketobj.ws_url
        self.num_chunks = num_chunks
        self.requestData = None
        self.ws_obj = websocketobj
        
    async def prepare_data(self):
        data = {}
        wsID = self.ws_obj.ws_ID
        requestID = uuid.uuid4().hex[:10]
        data['RequestID'] = requestID
        data['Query'] = {}
        data['Params'] = dict(ID=self.measurementID)

        websocketRouteID = '510'
        requestMessageProto = ParseDict(
            data, SubscribeResultsRequest(), ignore_unknown_fields=True)
        self.requestData = f'{websocketRouteID:4}{wsID:10}'.encode(
        ) + requestMessageProto.SerializeToString()
 
    async def subscribe(self):
        print("Subscribing to results")
        await self.prepare_data()

        counter = 0
        while counter < self.num_chunks:
            response = await self.ws_obj.handle_recieve(self.requestData, timeout_s=20)

            if response:
                #print(len(response))
                statusCode = response[10:13].decode('utf-8')
                if len(response) <= 13:
                    if statusCode != '200':
                        print("Status:", statusCode)
                else:
                    counter += 1
                    _id = response[0:10].decode('utf-8')
                    print("Data received; Chunk: "+str(counter) +
                          "; Status: "+str(statusCode))
                    with open('./result_'+str(counter)+'.bin', 'wb') as f:
                        f.write(response[13:])

        await self.ws_obj.handle_close()
        return


if __name__ == '__main__':
    measurementID = ''
    token = ''
    ws_url = ''
    num_chunks = 2
    sub = subscribeResults(measurementID, token, ws_url, num_chunks)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sub.subscribe())
