import asyncio
import base64
import functools
import json
import os
import requests
import time
from glob import glob

from dfxsnippets.adddata_pb2 import DataRequest
from dfxsnippets.websocketHelper import WebsocketHandler


class addData():
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

    @property
    def num_chunks(self):
        return len(self.chunks)

    def prepare_data(self):
        total_num_payload = len(glob(os.path.join(self.input_directory, 'payload*.bin')))
        total_num_meta = len(glob(os.path.join(self.input_directory, 'metadata*.bin')))
        total_num_properties = len(glob(os.path.join(self.input_directory, 'properties*.json')))
        if total_num_meta != total_num_payload != total_num_properties:
            raise ValueError('Missing files')
        for i in range(total_num_payload):
            with open(os.path.join(self.input_directory, 'payload' + str(i) + '.bin'), 'rb') as input_file:
                fileContent = input_file.read()
                payload = fileContent
            with open(os.path.join(self.input_directory, 'metadata' + str(i) + '.bin'), 'r') as input_file:
                meta = json.load(input_file)
            with open(os.path.join(self.input_directory, 'properties' + str(i) + '.json'), 'r') as input_file:
                properties = json.load(input_file)
            if i == 0 and total_num_payload > 1:
                action = 'FIRST::PROCESS'
            elif i == total_num_payload - 1:
                action = 'LAST::PROCESS'
            else:
                action = 'CHUNK::PROCESS'

            if (meta["dfxsdk"] < "4.0"):
                chunkOrder = properties['chunkNumber']
                startTime = properties['startTime_s']
                endTime = properties['endTime_s']
            else:
                chunkOrder = properties['chunk_number']
                startTime = properties['start_time_s']
                endTime = properties['end_time_s']
            duration = properties['duration_s']

            if self.conn_method == 'REST':  # For using REST
                data = {}
                data["ChunkOrder"] = chunkOrder
                data["Action"] = action
                data["StartTime"] = startTime
                data["EndTime"] = endTime
                data["Duration"] = duration
                # Additional meta fields !
                meta['Order'] = chunkOrder
                meta['StartTime'] = startTime
                meta['EndTime'] = endTime
                meta['Duration'] = duration

                data['Meta'] = json.dumps(meta)
                data["Payload"] = base64.b64encode(payload).decode('utf-8')

            else:  # For using websockets
                data = DataRequest()  # Reconfigure each chunk into a protocol buffer
                paramval = data.Params
                paramval.ID = self.measurementID

                data.ChunkOrder = chunkOrder
                data.Action = action
                data.StartTime = startTime
                data.EndTime = endTime
                data.Duration = duration
                # Additional meta fields !
                meta['Order'] = chunkOrder
                meta['StartTime'] = startTime
                meta['EndTime'] = endTime
                meta['Duration'] = data.Duration

                data.Meta = json.dumps(meta).encode()
                data.Payload = bytes(payload)

            self.chunks.append(data)

    def sendSync(self):
        if self.conn_method == 'REST':
            url = self.server_url + "/measurements/" + self.measurementID + "/data"
            headers = dict(Authorization="Bearer {}".format(self.token))
            headers['Content-Type'] = "application/json"
            for chunk in self.chunks:
                response = requests.post(url, json=chunk, headers=headers)
                print("*" * 10)
                print("addData response code: ", response.status_code)
                print("addData response body: ", response.json())
                print("*" * 10)
                if "LAST" not in chunk['Action']:
                    print("sleep for the chunk duration")
                    time.sleep(chunk['Duration'])

    async def sendAsync(self):
        if self.conn_method == 'REST':
            url = self.server_url + "/measurements/" + self.measurementID + "/data"
            headers = dict(Authorization="Bearer {}".format(self.token))
            headers['Content-Type'] = "application/json"
            for chunk in self.chunks:
                requestFunction = functools.partial(requests.post, url=url, json=chunk, headers=headers)
                loop = asyncio.get_event_loop()
                future = loop.run_in_executor(None, requestFunction)
                response = await future
                print("*" * 10)
                print("addData response code: ", response.status_code)
                print("addData response body: ", response.json())
                print("*" * 10)
                if "LAST" not in chunk['Action']:
                    print("sleep for the chunk duration")
                    await asyncio.sleep(chunk['Duration'])

        else:
            actionID = '0506'
            wsID = self.ws_obj.ws_ID
            for chunk in self.chunks:
                content = f'{actionID:4}{wsID:10}'.encode() + chunk.SerializeToString()
                await self.ws_obj.handle_send(content)
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
                print("*" * 10)
                print("addData response code: ", status_code)
                print("addData response body: ", response)
                print("*" * 10)
                if status_code != '200':
                    print("Error adding data. Please check your inputs.")
                    return
                if "LAST" not in chunk.Action:
                    print("sleep for the chunk duration")
                    await asyncio.sleep(chunk.Duration)


if __name__ == '__main__':
    # provide your MeasurementID and token "
    token = ''
    MeasurementID = ''
    server_url = ''
    ws_url = ''
    input_directory = ''
    websocketobj = WebsocketHandler(token, ws_url)
    addD = addData(MeasurementID, token, server_url, websocketobj, input_directory)

    # addD.sendSync()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(addD.sendAsync())
