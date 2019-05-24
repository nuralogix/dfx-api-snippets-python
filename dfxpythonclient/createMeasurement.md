# createMeasurement

This class shows one way to create a DeepAffex Measurement.

It depends upon the following packages:

```python
import json     # to jsonify the request body from dictionary
import requests # to send http request (install using pip)
```

## Basic usage

Create the object by providing the studyID, token, and URL. Call `.create()` to
get the `measurementID` as the return value

```python
cm_obj = createMeasurement(studyID, token, rest_url, resolution=0)
measurementID = cm_obj.create()
```

*Notice how we set `resolution=0`, which is the default value. It means that you
will get the average result back for this measurement, e.g. average heart rate
of the durarion. If you want to have the results come back as vectors, usually
time series, you can set `resolution=100`*

## Understanding the class

### Constructor

Let's examine the constructor. It requires a `studyID`, a token issued by the
Deepaffex server, and the URL of the REST API in use.

```python
def __init__(self, studyID, token, rest_url):
    self.studyID = studyID
    self.token = token
    self.rest_url = rest_url
    self.resolution = resolution
```

### `create`

The `create()` method of the class will then prepare the request header and body
and send the request. Here are the steps it takes...

1. Creates the URL for the endpoint

    ```python
    url = self.rest_url + "/measurements"
    ```

2. Embeds the token in the header:

    ```python
    headers = dict(Authorization="Bearer {}".format(self.token))
    ```

3. Prepare the request in dictionary format

    ```python
    data = {}
    data["StudyID"] = self.studyID
    data["Action"] = self.token
    data["Resolution"] = self.resolution
    ```

4. Sends the request with a JSON body and the headers to the URL

    ```python
    response = requests.post(url, data=json.dumps(data), headers=headers)
    ```
