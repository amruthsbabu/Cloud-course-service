import os
import boto3
from flask import Flask, jsonify
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

app = Flask(__name__)

# X-Ray configuration (optional)
ENABLE_XRAY = os.environ.get("ENABLE_XRAY", "false").lower() == "true"
if ENABLE_XRAY:
    xray_recorder.configure(service="course-service", context_missing="LOG_ERROR")
    XRayMiddleware(app, xray_recorder)

# Environment configuration
REGION = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION", "ap-south-2")

# DynamoDB setup (IRSA credentials)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
courses_table = dynamodb.Table("ammu-course")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "course-service"}), 200


@app.route("/courses/<id>", methods=["GET"])
def get_course(id):
    try:
        resp = courses_table.get_item(Key={"code": id})
        item = resp.get("Item")
        
        if not item:
            return jsonify({"error": "Course not found"}), 404
            
        return jsonify(item), 200
        
    except Exception as e:
        app.logger.error(f"Error fetching course {id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/courses", methods=["GET"])
def list_courses():
    try:
        resp = courses_table.scan(Limit=50)
        return jsonify(resp.get("Items", [])), 200
    except Exception as e:
        app.logger.error(f"Error listing courses: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=False)