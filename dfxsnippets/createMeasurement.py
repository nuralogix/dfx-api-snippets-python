import json
import datetime

import requests


class createMeasurement():
    def __init__(self, studyID, token, rest_url, mode, resolution=0):
        self.studyID = studyID
        self.token = token
        self.rest_url = rest_url
        self.resolution = resolution
        self.mode = mode

    def create(self):
        createMeaResults = []
        url = self.rest_url + "/measurements"
        data = {}
        data["StudyID"] = self.studyID
        data["Action"] = self.token
        data["Resolution"] = self.resolution
        data["Mode"] = self.mode

        headers = dict(Authorization="Bearer {}".format(self.token))
        headers['Content-Type'] = "application/json"
        try:
            response = requests.post(url, data=json.dumps(data), headers=headers)
        except:
            raise ValueError(' Cannot create measurement on server')
        print("*" * 10)
        createMeaTime = datetime.datetime.now().time()
        print("createMeasurement time: ", createMeaTime)
        createMeaResults.append(createMeaTime)
        print("createMeasurement response code: ", response.status_code)
        print("createMeasurement response body: ", response.json())
        print("*" * 10)
        
        try:
            measurementID = response.json()['ID']
            createMeaResults.append(measurementID)
            # return measurementID
            return createMeaResults
        except:
            raise ValueError(' Cannot create measurement on server')


if __name__ == '__main__':
    # provide your MeasurementID and token "
    studyID = ''
    token = ''
    rest_url = ''
    mode = ''
    cm = createMeasurement(studyID, token, rest_url, mode, resolution=0)
    cm.create()
