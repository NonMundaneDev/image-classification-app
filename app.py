import json
import boto3
import datetime
import numpy as np
import PIL.Image as Image
import uuid
import pytz


import tensorflow as tf

from urllib.parse import unquote
from pathlib import Path
from decimal import Decimal
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime as dt


# Get date and time as date of lambda function execution
# Change the timezone to your own timezone (if needed)
# Check out the list of timezones at: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

tz = pytz.timezone('Africa/Lagos')
date_time = str(dt.now(tz).strftime('%Y-%m-%d %H:%M:%S'))

date = date_time.split(" ")[0]
time = date_time.split(" ")[1]

timestamp = Decimal(str(dt.timestamp(dt.now())))

# Define path to load model from the directory you created with the Dockerfile
import_path = "model/"

# Load model from model path
model = tf.keras.models.load_model(import_path)

# Presets for input image shape
IMAGE_WIDTH = 224
IMAGE_HEIGHT = 224

# Define image properties
IMAGE_SHAPE = (IMAGE_WIDTH, IMAGE_HEIGHT)

# Set resources
s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')

# Select dynamodb table
table = dynamodb.Table('<REPLACE WITH TABLE NAME>')

def lambda_handler(event, context):

  bucket_name = event['Records'][0]['s3']['bucket']['name']
  key = unquote(event['Records'][0]['s3']['object']['key'])

  # In case client uploads an image with the same name, object will be versioned...
  # ... instead of overwritten.
  versionId = unquote(event['Records'][0]['s3']['object']['versionId'])


  # These were the class names used to build the model.
  # African armyworm --> 'AAW'
  # Egyptian cotton leafworm --> 'ECLW'
  # Fall Armyworm --> 'FAW'
  class_names = ['AAW', 'ECLW', 'FAW']
  
  # Printing the key to help if there's a need to debug using the logs.
  print(key)
  
  
  # Preprocess image before feeding it to the model
  # Input layer of the model expects an image size of 224 by 224
  image = readImageFromBucket(key, bucket_name).resize((224, 224))
  image = image.convert('RGB')
  image = np.asarray(image)
  image = image.flatten()
  image = image.reshape(1, 224, 224, 3)

  # Make prediction with the model
  # Ideally takes less than 15 ms on an x86 CPU to return result
  prediction = model.predict(image)
  print(prediction) # Optional print statement (useful during log inspection)
  pred_probability = "{:2.0f}%".format(100*np.max(prediction))
  index = np.argmax(prediction[0], axis=-1)
  print(index) # Optional print statement (useful during log inspection)
  predicted_class = class_names[index]

  # Print image name stored in S3 and the predicted class to run tests.
  print('ImageName: {0}, Model Prediction: {1}'.format(key, predicted_class))

  # URL of the image predicted, so it can be added to the database
  img_url = f"https://<NAME OF BUKCET FOR INFERENCE IMAGES>.s3.<REGION>.amazonaws.com/{key}?versionId={versionId}"


  # The code below checks if the predicted class is available in the DB for a particular day.
  # If its available, the code updates the count of the class.
  # If it is not available, the code enters a new entry for that day.

  for i in class_names:

    if predicted_class == i: 
      # Using scan is ineffectie and costly if your DB will hold a lot of items.
      # Try using query or the GetItem or BacthGetItem APIs.
      details = table.scan(
          FilterExpression=Key('PredictionDate').eq(date) 
          & Attr("ClassName").eq(predicted_class),
          Limit=123,
      )

      if details['Count'] > 0 and details['Items'][0]['ClassName'] == predicted_class:

        event = max(details['Items'], key=lambda ev: ev['Count_ClassName'])

        current_count = event['Count_ClassName']
                    
        print(current_count) # Optional print statement (useful during log inspection)
  
        updated_count = current_count + 1
          
        table_items = table.put_item(
              Item={
              'PredictionDate': date,
              'ClassPredictionID': predicted_class + "-" + str(uuid.uuid4()), # generate unique prediction ID
              'ClassName': predicted_class,
              'Count_ClassName': updated_count,
              'CaptureTime': time,
              'ImageURL_ClassName': img_url,
              'ConfidenceScore': pred_probability
            }
          )
        print("Updated existing object...")
        return table_items
    
    # If there are 0 counts for the moth uploaded today for prediction,
    # Enter a fresh item into the database.
      elif details['Count'] == 0:
        new_count = 1
        table_items = table.put_item(
              Item={
                'PredictionDate': date,
                'ClassPredictionID': predicted_class + "-" + str(uuid.uuid4()), # generate unique prediction ID
                'ClassName': predicted_class,
                'Count_ClassName': new_count,
                'CaptureTime': time,
                'ImageURL_ClassName': img_url,
                'ConfidenceScore': pred_probability
              }
            )
        print(f"Added new object to {table.name}!")
        return table_items

  print("Updated model predictions successfully!")
   

def readImageFromBucket(key, bucket_name):
  """
  Read the image from the triggering bucket.
  :param key: object key
  :param bucket_name: Name of the triggering bucket.
  :return: Pillow image of the object.

  """
  # Reading the object from 
  bucket = s3.Bucket(bucket_name)
  object = bucket.Object(key)
  response = object.get()
  return Image.open(response['Body'])