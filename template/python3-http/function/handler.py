from flask import current_app


@current_app.route("/additional_route", methods=["GET"])
def cacca():
    return {"statusCode": 200, "body": "Hello from additional_route"}

def handle(event, context):
    return {"statusCode": 200, "body": "Hello from OpenFaaS!"}
