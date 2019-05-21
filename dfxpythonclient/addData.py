import functools
import asyncio
import base64
import requests
import json
import time
from glob import glob
import os


class addData():
    def __init__(self, measurementID, token, server_url, input_directory):
        self.measurementID = measurementID
        self.token = token
        self.server_url = server_url
        self.input_directory = input_directory
        self.chunks = []
        self.prepare_data()

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
            payload = base64.b64encode(fileContent).decode('utf-8')
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
            response = requests.post(url, json=chunk, headers=headers)
            print("*"*10)
            print("addData response code: ", response.status_code)
            print("addData response body: ", response.json())
            print("*"*10)
            if "LAST" not in chunk['Action']:
                print("sleep for the chunk duration")
                time.sleep(chunk['Duration'])

    async def sendAsync(self):
        url = self.server_url + "/measurements/"+self.measurementID+"/data"
        headers = dict(Authorization="Bearer {}".format(self.token))
        headers['Content-Type'] = "application/json"
        for chunk in self.chunks:
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
        return response


if __name__ == '__main__':
    # provide your MeasurementID and token "
    token = ''
    MeasurementID = ''
    server_url = ''
    input_directory = ''
    addD = addData(MeasurementID, token, server_url, input_directory)

    # addD.sendSync()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(addD.sendAsync())
