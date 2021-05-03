import boto3

from common.json_utils import clean_json

sagemaker_client = boto3.client('sagemaker')

def lambda_handler(event, context):
    training_name = event['training_info']['TrainingJobName']
    training_info = sagemaker_client.describe_training_job(TrainingJobName=training_name)
    event['training_info'] = clean_json(training_info)
    return event
