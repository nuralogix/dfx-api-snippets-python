# websocketHandler

This class handles all WebSocket activity within the DFX API. Instead of having the user manually set up the WebSockets, this class handles all the calls and responses. Also, this class enables sending and receiving all in one WebSocket connection, through asynchronous programming.

It depends upon the following packages:

```python
import asyncio    # Asynchronous io
import json       # For handling json formats
import uuid       # Used to generate uuid
import websockets # Websockets library
```

**Basic usage:**

Create the WebsocketHandler object with an API token (can be user token or device token) and websocket url.

```python
ws_obj = WebsocketHandler(token, websocket_url)
```

Then set up an `asyncio` event loop, and make the WebSocket connection with:

```python
loop = asyncio.get_event_loop()
loop.run_until_complete(ws_obj.connect_ws())
```

Now that your WebSocket connection is made, you can call the `ws_obj.handle_send()` and `ws_obj.handle_receive()` methods to send and receive DFX API messages. Finally, to close the WebSocket connection, run `ws_obj.handle_close()`. All of these methods are awaitable, meaning they must be called with `await ws_obj.__method__()` or inside an asyncio event loop.

**Documentation:**

The constructor class takes in an API token (can be user token or device token) and a WebSocket url (e.g. `wss://api.deepaffex.ai:9080`). It creates the header by formatting the token, and generates a 10-digit WebSocket ID. It initially sets the WebSocket connection `self.ws` to `None`.

Next, we have a boolean `self.recv` used to create a mutual exclusion lock for receiving (more on that below). Then we created multiple lists (stacks) for storing different types of API responses from the WebSocket.

Finally, we create a dictionary to store the websocketID and the message body from all messages that come from an unknown WebSocket connection.

```python
def __init__(self, token, websocket_url):
    self.token = token
    self.ws_url = websocket_url
    self.headers = dict(Authorization="Bearer {}".format(self.token))
    self.ws_ID = uuid.uuid4().hex[:10]      # Use same ws_ID for all connections
    self.ws = None

    # Use this to form a mutual exclusion lock
    self.recv = True

    # Lists for tracking return values
    self.addDataStats = []
    self.subscribeStats = []
    self.chunks = []
    self.unknown = {}        # For storing messages not coming from a known websocket sender
```

Now let's look at the methods for handling connect and disconnect. The WebSocket connection is opened by calling `ws = await websockets.client.connect(self.ws_url, extra_headers=self.headers)`, where the `self.headers` is the header generated in `__init__()`. The method `handle_connect(self)` return the WebSocket connection while `connect_ws(self)` connects the `self.ws` object.

```python
async def connect_ws(self):
    if not self.ws:
        self.ws = await self.handle_connect()

async def handle_connect(self):
    ws = await websockets.client.connect(self.ws_url, extra_headers=self.headers)
    print(" Websocket Connected ")
    return ws
```

The WebSocket is closed by calling `await self.ws.close()`.

```python
async def handle_close(self):
    print(" Closing Websocket ")
    await self.ws.close()
    return
```

Sending messages is straightforward and only involves a call of `await self.ws.send(content)`. This method assumes that the WebSocket connection has already been made. It will give an error if there is no WebSocket connection.

```python
async def handle_send(self, content):
    await self.ws.send(content)

```

Receiving, however, is much more complex. For one WebSocket connection in one thread, there can be at most one call of `ws.recv()` at any given time, otherwise an error will be raised. Therefore, we utilize a mutual exclusion lock using a boolean `self.recv`. In order to make the `ws.recv()` call, we first check if `self.recv == True`. If yes, then we form a lock around `response = await self.ws.recv()` by setting `self.recv = False` first and then `self.recv = True` when it is done. Otherwise, the method returns nothing.

```python
if self.recv == True:
    self.recv = False
    response = await self.ws.recv()
    self.recv = True
else:
    return
```

*Since `handle_recieve(self)` only makes one `recv()` call at a time, and returns nothing when a `recv()` call cannot be made, it is recommended that you call this method in a polling while loop, for example:*

```python
while True:
    await self.ws_obj.handle_recieve()
    if (...):
        ...
        break
```

If there is a `response`, it first decodes the wsID from the response by calling `wsID = response[0:10].decode('utf-8')`. (Reminder that all DFX API websocket responses come in the form `Buffer( [ string:10 ][ string:3 ][ string/buffer ] )`). If the `wsID` is not recognized (i.e. not equal to the `self.ws_ID` for the current connection), we store the wsID and response body into a dictionary called `self.unknown`.

```python
wsID = response[0:10].decode('utf-8')
if wsID != self.ws_ID:
    self.unknown[wsID] = response
```

Finally, we need to sort the responses by type, to determine whether this is an API response from add_data or subscribe_to_results (either status or chunk). This can be done by checking the length of each message. The specific values are stored inside the `default.config` file. It would then add each message into the appropriate list / stack, which would then be retrieved by a parent function.

```python
with open('./default.config') as json_file:
    data = json.load(json_file)

    if len(response) == int(data["Subscribe_status"]):
        self.subscribeStats.append(response)
    elif len(response) <= int(data["Adddata_status"]):
        self.addDataStats.append(response)
    else:
        self.chunks.append(response)
```
