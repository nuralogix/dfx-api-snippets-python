import asyncio
import uuid
import websockets


class WebsocketHandler():
    def __init__(self, token, websocket_url):
        self.token = token
        self.ws_url = websocket_url
        self.headers = dict(Authorization="Bearer {}".format(self.token))
        self.ws = None
        self.ws_ID = uuid.uuid4().hex[:10]      # Use same ws_ID for all connections
        self.ws_IDs = []
        self.buffer = []        # For storing messages not coming from a known websocket sender

        # Bools for keeping track of things
        self.sent_req = False
        self.recv1 = True
        self.recv2 = True

    async def handle_connect(self):
        try:
            ws = await websockets.client.connect(self.ws_url, extra_headers=self.headers)
        except:
            raise Exception("Cannot connect to websocket")
        print(" Websocket Connected ")
        return ws

    async def handle_close(self):
        print(" Closing Websocket ")
        await self.ws.close()
        return

    async def handle_send(self, actionID, content):
        if self.ws == None:
            self.ws = await self.handle_connect()
        await self.ws.send(content)
        while True:
            if self.recv1 == True:       # Only receive here when other side is not receiving
                response = await self.ws.recv()
                if response:
                    self.recv2 = True
                    break
            else:
                await asyncio.sleep(1)
        self.recv1 = False
        return response

    async def handle_recieve(self, data, timeout_s=20):
        await asyncio.sleep(0.5)  # Must wait for websocket to connect, also time spacing for polling
        if self.ws == None:
            self.ws = await self.handle_connect()

        if self.sent_req == False:
            await self.ws.send(data)
            self.sent_req = True

        while True:     # Poll until a response is received
            await asyncio.sleep(0.5)    # Time spacing for polling, must wait for other things to run

            # Block to ensure that only this part can receive
            self.recv1 = False
            if self.recv2:
                response = await self.ws.recv()
                if response:
                    break
            self.recv1 = True

        if response:
            wsID = response[0:10].decode('utf-8')
            if wsID != self.ws_ID:      # For handling messages not sent by this websocket connectionself.ws_IDs
                self.ws_IDs.append(wsID)
                self.buffer.append(response)

            if len(response) > 13:
                self.recv2 = False
            return response
