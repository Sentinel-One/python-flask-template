def handle(event, context):
    return {"statusCode": 200, "body": "Hello from OpenFaaS!"}

def action(event, context):
    return {"statusCode": 200, "body": "Hello from Action!"}
