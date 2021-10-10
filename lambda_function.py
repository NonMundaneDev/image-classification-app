"""
This Lambda function enables API Gateway to use the GET and DELETE methods on your
dynamodb table.

Client <--> API Gateway <--> Lambda func <--> DynamoDB Table
"""

import json
import boto3
import pprint
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('<Enter Table Name Here>') #define which dynamodb table to access

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        
        return json.JSONEncoder.default(self, obj)
        
def query_table(ClassToFind):
    queryreturn = table.query(                    # perform query
        IndexName="ClassName-globo-index",
        KeyConditionExpression= Key("ClassName").eq(ClassToFind),
        ScanIndexForward=False
    )
    return queryreturn
    

def delete_item_operation(ClassPredictionID):
    queryreturn = table.query(                    # perform query
          IndexName="ClassID-globo-index",
          KeyConditionExpression= Key("ClassPredictionID").eq(ClassPredictionID)
        )

    if not queryreturn['Items']:
            not_found = "NOT_FOUND: Class details not found in the database."
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Credentials': 'true',
                    'Content-Type': 'application/json'
                        },
                'body': json.dumps(not_found, indent=4, cls = DecimalEncoder)
                        }
        
    elif queryreturn['Items']:
        date = str(queryreturn['Items'][0]['PredictionDate'])
        try:
            response = table.delete_item(
                Key={
                    'PredictionDate': date,
                    'ClassPredictionID': ClassPredictionID
                },
                ConditionExpression = "attribute_exists(ClassPredictionID)",
                ReturnValues="ALL_OLD"
            )
        except ClientError as e:
            if e.response['Error']['Code'] == "ConditionalCheckFailedException":
                error = "Delete class details FAILED:" + " Moth item does not exist in the database."
                return {
                    'statusCode': 500,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                        'Access-Control-Allow-Credentials': 'true',
                        'Content-Type': 'application/json'
                            },
                    'body': json.dumps(error, indent=4, cls = DecimalEncoder)
                        }
                
            else:
                raise e
        else:
            if 'Attributes' in response:
                success = "SUCCESS: Moth item deleted successfully from the database."
                return {
                    'statusCode': 200,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                        'Access-Control-Allow-Credentials': 'true',
                        'Content-Type': 'application/json'
                            },
                    'body': json.dumps(success, indent=4, cls = DecimalEncoder)
                        }

            else:
                return "Class details not found in the database."
            

def delete_all_items():
    scan = table.scan()
    with table.batch_writer() as batch: 
        for item in scan['Items']:
            batch.delete_item(Key={'PredictionDate': item['PredictionDate'],
                    'ClassPredictionID': item['ClassPredictionID']})
    del_all_success = "SUCCESS: Deleted all class details successfully."
    return {
            'statusCode': 200,
            'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Credentials': 'true',
                    'Content-Type': 'application/json'
                        },
            'body': json.dumps(del_all_success, indent=4, cls = DecimalEncoder)
            }   

def get_operation(ClassName):
    
    if str(ClassName) == "AAW":
        aaw_data = query_table('AAW')
        response = aaw_data['Items']

    elif str(ClassName) == "ECLW":
        eclw_data = query_table('ECLW')
        response = eclw_data['Items']

    elif str(ClassName) == "FAW":
        faw_data = query_table('FAW')
        response = faw_data['Items']
        
    elif str(ClassName) == "ALL":
        body = table.scan()
        response = body['Items']
    
    else:
        return {
            'statusCode': '404',
            'body': 'Class not found.'
            }
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Credentials': 'true',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(response, indent=4, cls = DecimalEncoder)
    }

def lambda_handler(event, context):
    
    operation = event['httpMethod']
    if operation == 'GET':
        ClassName = event['queryStringParameters']['ClassName']
        return get_operation(ClassName)
        
    elif operation == 'DELETE':
        try:
            if str(event['queryStringParameters']['DeleteAll']) == "ALL":
                return delete_all_items()
                
        except KeyError:
            ClassPredictionID = event['queryStringParameters']['ClassPredictionID']
            return delete_item_operation(ClassPredictionID)
        
    else:
        return None
        
 
 

    
    