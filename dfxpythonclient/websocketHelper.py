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

        # Bools for keeping track of things
        self.recv1 = True

        # Lists for tracking return values
        self.addDataStats = []
        self.subscribeStats = []
        self.chunks = []
        self.unknown = {}        # For storing messages not coming from a known websocket sender


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

    async def handle_send(self, content):
        if self.ws == None:
            self.ws = await self.handle_connect()
        await self.ws.send(content)

    async def handle_recieve(self):
        if self.recv1 == True:
            self.recv1 = False
            response = await self.ws.recv()
            self.recv1 = True
        else:
            return
        if response:
            wsID = response[0:10].decode('utf-8')
            # Sort out response messages by type
            if wsID != self.ws_ID:
                #print("Received a package that didn't come from a local sender")
                self.unknown[wsID] = response
            if len(response) == 13:
                #print("Status for subscribe to results")
                self.subscribeStats.append(response)
            elif len(response) == 53:
                #print("Status for addData")
                self.addDataStats.append(response)
            else:
                #print("Chunk for subscribe to results")
                self.chunks.append(response)
        return
