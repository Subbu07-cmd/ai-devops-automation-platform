"""AWS Lambda entry point (API Gateway / Function URL)."""
from mangum import Mangum

from app.main import app

handler = Mangum(app)
