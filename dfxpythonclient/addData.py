import functools
import asyncio
import base64
import requests
import json
import time
from glob import glob
import os
import uuid

from google.protobuf.json_format import ParseDict
from dfxpythonclient.adddata_pb2 import DataRequest
from dfxpythonclient.websocketHelper import WebsocketHandler

class addData():
    def __init__(self, measurementID, token, server_url, websocketobj, input_directory):
        self.measurementID = measurementID
        self.token = token
        self.server_url = server_url
        self.input_directory = input_directory
        self.chunks = []
        self.prepare_data()
        self.ws_obj = websocketobj

    @property
    def num_chunks(self):
        return len(self.chunks)

    def prepare_data(self):
        total_num_payload = len(
            glob(os.path.join(self.input_directory, 'payload*.bin')))
        total_num_meta = len(
            glob(os.path.join(self.input_directory, 'metadata*.bin')))
        total_num_properties = len(
            glob(os.path.join(self.input_directory, 'properties*.json')))
        if total_num_meta != total_num_payload != total_num_properties:
            raise ValueError('Missing files')
        for i in range(total_num_payload):
            with open(os.path.join(self.input_directory, 'payload' + str(i) + '.bin'), 'rb') as input_file:
                fileContent = input_file.read()
            #payload = base64.b64encode(fileContent).decode('utf-8')
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

            chunkOrder = properties['chunkNumber']
            startTime = properties['startTime_s']
            endTime = properties['endTime_s']
            duration = properties['duration_s']

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
            meta['Duration'] = data['Duration']

            data['Meta'] = json.dumps(meta)
            data["Payload"] = payload

            self.chunks.append(data)

    def sendSync(self):
        url = self.server_url + "/measurements/"+self.measurementID+"/data"
        headers = dict(Authorization="Bearer {}".format(self.token))
        headers['Content-Type'] = "application/json"
        for chunk in self.chunks:
            chunk["Payload"] = base64.b64encode(chunk["Payload"]).decode('utf-8')

            response = requests.post(url, json=chunk, headers=headers)
            print("*"*10)
            print("addData response code: ", response.status_code)
            print("addData response body: ", response.json())
            print("*"*10)
            if "LAST" not in chunk['Action']:
                print("sleep for the chunk duration")
                time.sleep(chunk['Duration'])
        print("Done adding data")

    async def sendAsync(self):
        url = self.server_url + "/measurements/"+self.measurementID+"/data"
        headers = dict(Authorization="Bearer {}".format(self.token))
        headers['Content-Type'] = "application/json"
        for chunk in self.chunks:
            chunk["Payload"] = base64.b64encode(chunk["Payload"]).decode('utf-8')

            requestFunction = functools.partial(
                requests.post, url=url, json=chunk, headers=headers)
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(None, requestFunction)
            response = await future
            print("*"*10)
            print("addData response code: ", response.status_code)
            print("addData response body: ", response.json())
            print("*"*10)
            if "LAST" not in chunk['Action']:
                print("sleep for the chunk duration")
                await asyncio.sleep(chunk['Duration'])
        print("Done adding data")

    async def sendWS(self):
        for chunk in self.chunks:
            data = DataRequest()
            paramval = data.Params
            paramval.ID = self.measurementID

            meta = {}
            data.ChunkOrder = chunk["ChunkOrder"]
            data.Action     = chunk["Action"]
            data.StartTime  = chunk["StartTime"]
            data.EndTime    = chunk["EndTime"]
            data.Duration   = chunk["Duration"]
            # Additional meta fields !
            meta['Order'] = chunk["ChunkOrder"]
            meta['StartTime'] = chunk["StartTime"]
            meta['EndTime'] = chunk["EndTime"]
            meta['Duration'] = data.Duration
            data.Meta = json.dumps(meta).encode()
            data.Payload = bytes(chunk["Payload"])

            actionID = '506'
            wsID = self.ws_obj.ws_ID
            content = f'{actionID:4}{wsID:10}'.encode() + data.SerializeToString()

            response = await self.ws_obj.handle_send(actionID, content)
            status_code = response[10:13].decode('utf-8')

            print("*"*10)
            print("addData response code: ", status_code)
            print("addData response body: ", response)
            print("*"*10)

            if "LAST" not in chunk['Action']:
                print("sleep for the chunk duration")
                await asyncio.sleep(chunk['Duration'])

            await self.ws_obj.ws_send.close()
            print(" Closing Websocket ", wsID)

        print("Done adding data")


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
