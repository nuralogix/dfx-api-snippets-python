# createMeasurement

This class is an example that shows one way to create a DeepAffex Measurement.

It depends upon the following packages:

```python
import json     # to jsonify the request body from dictionary
import requests # to send http request (install using pip)
```

Let's examine the constructor of the Class. It requires a studyID, a token issued by the Deepaffex server, and the url to the REST API in use.

```python
def __init__(self, studyID, token, rest_url):
    self.studyID = studyID
    self.token = token
    self.rest_url = rest_url
```

The `create()` method of the class will then prepare the request header and body and send the request. Here are the steps it takes...

Creates the url for the endpoint

```python
url = self.rest_url + "/measurements"
```

Embeds the token in the header:

```python
headers=dict(Authorization="Bearer {}".format(self.token))
```

Prepare the request in dictionary format

```python
data = {}
data["StudyID"] = self.studyID
data["Action"] = self.token
```
Then sends the request with a JSON body and the headers to the url

```python
response = requests.post(url,data=json.dumps(data), headers=headers) 
```