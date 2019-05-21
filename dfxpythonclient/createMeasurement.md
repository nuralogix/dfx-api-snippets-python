# Description about the createMeasurement Class

This class can be used to create a measurement. All you need is the studyID, the token you received from the "register/login" process, and the base url of the dfx api rest service

This class needs the follow packages:
```python
import requests #send http request
import json     #jsonify the request body from dictionay
```
Let's visit the constructor of the Class. It requires a studyID, a token issued by our API server, and a url to the rest api service.
```python
def __init__(self, studyID, token, rest_url):
    self.studyID = studyID
    self.token = token
    self.rest_url = rest_url
```
The `create()` method of the class will then prepare the request header and body and send the request.

create the url for the endpoint
```python
url = self.rest_url + "/measurements"
```
Embbed the token in the header:
```python
headers=dict(Authorization="Bearer {}".format(self.token))
```
prepare the request in dictionary format
```python
data = {}
data["StudyID"] = self.studyID
data["Action"] = self.token
```
Then send the request with json format body and the headers to the url
```python
response = requests.post(url,data=json.dumps(data), headers=headers) 
```
