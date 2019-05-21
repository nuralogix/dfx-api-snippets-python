import requests
import json


class createMeasurement():

    def __init__(self, studyID, token, rest_url):
        self.studyID = studyID
        self.token = token
        self.rest_url = rest_url

    def create(self):
        url = self.rest_url + "/measurements"
        data = {}
        data["StudyID"] = self.studyID
        data["Action"] = self.token

        headers = dict(Authorization="Bearer {}".format(self.token))
        headers['Content-Type'] = "application/json"
        try:
            response = requests.post(
                url, data=json.dumps(data), headers=headers)
        except:
            raise ValueError(' Can not create measurement on server')
            return ''
        print("*"*10)
        print("createMeasurement response code: ", response.status_code)
        print("createMeasurement response body: ", response.json())
        print("*"*10)
        measurementID = response.json()['ID']
        return measurementID


if __name__ == '__main__':
    # provide your MeasurementID and token "
    studyID = ''
    token = ''
    rest_url = ''
    cm = createMeasurement(studyID, token, rest_url)
    cm.create()
