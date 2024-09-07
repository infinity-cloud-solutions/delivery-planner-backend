import boto3
import json

# Initialize a session using Amazon DynamoDB
session = boto3.Session(
    aws_access_key_id='key',
    aws_secret_access_key='secret',
    region_name='us-east-1'
)

# Initialize DynamoDB resource
dynamodb = session.resource('dynamodb')

# Select your DynamoDB table
table_name = 'Orders'
table = dynamodb.Table(table_name)

# Load JSON data
with open('/data.json') as json_file:
    data = json.load(json_file)

# Insert data into DynamoDB table
with table.batch_writer() as batch:
    for item in data:
        batch.put_item(Item=item)

print("Data insertion complete.")
