import asyncio
import uuid
import websockets


class WebsocketHandler():
    def __init__(self, token, websocket_url):
        self.token = token
        self.ws_url = websocket_url
        self.headers = dict(Authorization="Bearer {}".format(self.token))
        self.ws_recv = None
        self.ws_send = None
        self.ws = None
        self.ws_ID = uuid.uuid4().hex[:10]      # Use same ws_ID for all connections
    

    async def connect_ws(self):
        try:
            ws = await websockets.client.connect(self.ws_url, extra_headers=self.headers)
        except:
            raise Exception("Cannot connect to websocket")
        print(" Websocket Connected ")
        return ws


    async def handle_send(self, actionID, content):
        if self.ws == None:
            self.ws = await self.connect_ws()
        await self.ws.send(content)
        while True:
            response = await self.ws.recv()
            if response != None:
                break
        return response


    async def handle_recieve(self, data, num_chunks=0, timeout_s=20):
        if self.ws == None:
            self.ws = await self.connect_ws()
        await self.ws.send(data)
        if num_chunks <= 0:
            raise Exception("No chunks or invalid number of chunks")

        wsID = data[4:14].decode('utf-8')
        counter = 0
        while True:
            try:
                response = await self.ws.recv()
            except asyncio.TimeoutError:
                response = ""
                print(" Closing Websocket ", wsID)
                await self.ws.close()
                return

            if response:
                statusCode = response[10:13].decode('utf-8')
                if counter == 0:
                    print("Status:", statusCode)
                else:
                    _id = response[0:10].decode('utf-8')
                    print("Data received; Chunk: "+str(counter) +
                          "; Status: "+str(statusCode))
                    with open('./result_'+str(counter)+'.bin', 'wb') as f:
                        f.write(response[13:])

            counter += 1
            if counter > num_chunks:
                print(" Closing Websocket ", wsID)
                await self.ws.close()
                return