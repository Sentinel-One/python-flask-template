#!/usr/bin/env python
import os, sentry_sdk
from flask import Flask, request, jsonify, json
from waitress import serve
from werkzeug.exceptions import HTTPException, abort
from sentry_sdk.integrations.flask import FlaskIntegration
import jsonschema
from function import handler, json_schema

if os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(os.environ["SENTRY_DSN"],
                    traces_sample_rate=0.2,
                    environment=os.environ.get("FLASK_ENV") or "development",
                    integrations=[FlaskIntegration()])

app = Flask(__name__)


class Event:
    def __init__(self):
        self.body = request.get_json(force=True)
        self.headers = request.headers
        self.method = request.method
        self.query = request.args
        self.path = request.path


class Context:
    def __init__(self):
        self.hostname = os.getenv("HOSTNAME", "localhost")


def format_status_code(resp):
    if "statusCode" in resp:
        return resp["statusCode"]

    return 200


def format_body(resp):
    if "body" not in resp:
        return ""
    elif type(resp["body"]) == dict:
        return jsonify(resp["body"])
    else:
        return str(resp["body"])


def format_headers(resp):
    if "headers" not in resp:
        return []
    elif type(resp["headers"]) == dict:
        headers = []
        for key in resp["headers"].keys():
            header_tuple = (key, resp["headers"][key])
            headers.append(header_tuple)
        return headers

    return resp["headers"]


def format_response(resp):
    if resp is None:
        return ("", 200)

    statusCode = format_status_code(resp)
    body = format_body(resp)
    headers = format_headers(resp)

    return (body, statusCode, headers)


@app.route("/", defaults={"path": ""}, methods=["GET", "PUT", "POST", "PATCH", "DELETE"])
@app.route("/<path:path>", methods=["GET", "PUT", "POST", "PATCH", "DELETE"])
def call_handler(path):
    event = Event()
    context = Context()

    if hasattr(json_schema,'payload_schema'):
        try:
            jsonschema.validate(event.body, json_schema.payload_schema, format_checker=jsonschema.draft7_format_checker)
        except jsonschema.exceptions.ValidationError as err:
            e = {"type": "VALIDATION_ERROR", "title": "The current JSON Body obejct does not conform with the JSON Schema", "status": 502, "detail": err.message}
            response = jsonify(e)
            response.status_code = e["status"]
            abort(response)

    response_data = handler.handle(event, context)

    resp = format_response(response_data)
    return resp


@app.errorhandler(HTTPException)
def handle_exception(e):

    response = e.get_response()

    if response.content_type != "application/json":
        response.data = json.dumps(
            {
                "type": "UNKNOWN",
                "title": e.name,
                "status": e.code or 500,
                "detail": e.description if type(e.description) is str else "Flask Internal",
            }
        )

        response.content_type = "application/json"

    if (e.code or 500) >= 500:
        sentry_sdk.capture_exception(e)

    return response


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000)
