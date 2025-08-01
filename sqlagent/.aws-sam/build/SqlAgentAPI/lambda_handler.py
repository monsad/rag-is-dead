"""
AWS Lambda handler for FastAPI deployment
"""
from mangum import Mangum
from api import app

# Create the Lambda handler
handler = Mangum(app, lifespan="off")

# For AWS Lambda deployment
def lambda_handler(event, context):
    return handler(event, context)