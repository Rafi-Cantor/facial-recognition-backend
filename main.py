from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
from botocore.exceptions import ClientError

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
UPLOAD_BUCKET = "facial-recognition-app-upload-bucket"
DYNAMO_DB_TABLE = "faceprints"
COLLECTION_ID = "facial-recognition-app"

s3_resource = boto3.resource("s3")
rekognition = boto3.client("rekognition",region_name='eu-west-2' )
dynamodb = boto3.client("dynamodb",region_name='eu-west-2' )

app = Flask(__name__)
CORS(app, origins='*')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload_new_profile', methods=["PUT"])
def upload_new_profile():
    try:
        image = request.files["image"]
        full_name = request.form["full_name"]
    except KeyError:
        return jsonify({"error_message": "Please supply a full name and an image. "}), 400
    if not allowed_file(image.filename):
        return jsonify({"error_message": "File type not allowed. "}), 400

    image_bytes = image.read()
    image.seek(0)
    try:
        response = rekognition.detect_faces(
            Image={"Bytes": image_bytes}
        )
    except ClientError as e:
        if e.response['Error']["Code"] == 'ValidationException':
            message = "There should be only 1 face in the image!"
        else:
            message = e.response['Error']['Message']
        return jsonify({"error_message": message}), 400
    else:
        number_of_faces = len(response['FaceDetails'])
        if number_of_faces != 1:
            return jsonify({"error_message": f"Image should have one face! "}), 400

        s3_resource.Object(UPLOAD_BUCKET, image.filename).put(Body=image, Metadata={'full_name': full_name})
        return jsonify({"message": f"Image of {full_name} has been uploaded! "}), 201


@app.route('/upload_for_recognition', methods=["POST"])
def upload_for_recognition():
    try:
        image = request.files["image"]
    except KeyError:
        return jsonify({"error_message": "Please supply an image! "}), 400
    if not allowed_file(image.filename):
        return jsonify({"error_message": "File type not allowed. "}), 400
    image_bytes = image.read()
    try:
        response = rekognition.search_faces_by_image(
            CollectionId=COLLECTION_ID,
            Image={"Bytes": image_bytes}
        )
    except ClientError as e:
        if e.response['Error']["Code"] == 'ValidationException':
            message = "There should be only 1 face in the image"
        else:
            message = e.response['Error']['Message']
        return jsonify({"error_message": message}), 400
    else:
        face_matches = []
        for match in response['FaceMatches']:
            face_id = match['Face']['FaceId']
            face = dynamodb.get_item(
                TableName=DYNAMO_DB_TABLE,
                Key={'face_id': {'S': face_id}}
            )

            face_matches.append({
                "face_id": face["Item"]["face_id"]["S"],
                "full_name": face["Item"]["full_name"]["S"]
            })

        if len(face_matches) == 0:
            face_matches = None

        return jsonify({"face_matches": face_matches}), 201


if __name__ == '__main__':
    app.run(debug=False, port=5000)

