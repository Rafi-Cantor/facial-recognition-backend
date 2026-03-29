## Facial Recognition — Backend

Python Flask API for a facial recognition app. Handles image validation, S3 uploads, and face matching via AWS Rekognition and DynamoDB.

### Install dependencies
```
pip install -r requirements.txt
```

### Run
```
python main.py
```

### In production
Replace asterisk in cores with frontend URL
```
CORS(app, origins='*')
```


