''' This lambda function boostraps the sagemaker crossvalidation training process.

Bootstrap steps:
 - Generate a timestamp based run_id that will be used to identify this crossvalidation process
 - Create a training name template that will be filled with the split name by split_preparer function
 - Create or load a SageMaker Experiment that will be used as a container for all trainings
 - Create a SageMaker Experiment Trial that will be used as a container for the trainings in this 
   cross-validation run
'''

import datetime
import logging
import json

import botocore
import smexperiments
from smexperiments.experiment import Experiment
from smexperiments.trial import Trial
import jsonschema

from errors import InputValidationError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info(f'botocore version: {botocore.__version__}')
logger.info(f'SageMaker Experiment version: {smexperiments.__version__}')
logger.info(f'jsonschema version: {jsonschema.__version__}')

# Resources are deployed as lambda layers and lambda layers will be mapped
# to /opt directory in lambda runtime
input_schema_path = '/opt/resources/schemas/input.schema.json'

def get_experiment(experiment_name, tags=[], create_if_not_exists=False):
    try:
        experiment = Experiment.load(experiment_name=experiment_name)
        logger.info(f'Using existing experiment: {experiment_name}')
    except botocore.exceptions.ClientError as e:
        if (e.response['Error']['Code'] == 'ResourceNotFound') and create_if_not_exists:
            experiment = Experiment.create(
                experiment_name=experiment_name, 
                description=f'SageMaker Experiment to analyze cross-validated training results',
                tags=tags
            )
            logger.info(f'Created new experiment: {experiment_name}')
        else:
            raise e
    return experiment

def get_trial(experiment_name, trial_name, tags=[], create_if_not_exists=False):
    try:
        trial = Trial.load(trial_name=trial_name)
        logger.info(f'Using existing trial: {trial_name}')
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFound':
            trial = Trial.create(
                experiment_name=experiment_name,
                trial_name=trial_name,
                tags=tags
            )
            logger.info(f'Created new trial: {trial_name}')
        else:
            raise e
    return trial

def get_job_name(name, run_id):
    job_name = f'crossvalidator-{name}-{run_id}'
    logger.info(f'Crossvalidator job name: {job_name}')
    return job_name

def get_training_name_template(job_name):
    training_name_template = f'{job_name}-${{fold_name}}'
    logger.info(f'Training template name: {training_name_template}')
    return training_name_template

def validate_input(event, schema_path):
    with open(schema_path) as f:
        schema = json.load(f)
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(event), key=lambda e: e.path)
    if errors:
        raise InputValidationError(errors)

def lambda_handler(event, context):
    validate_input(event, schema_path=input_schema_path)
    job_config = event['job_config']
    training_info = event['training']
    name = job_config['name']
    tags = job_config.get('tags', [])
    experiment_name = job_config.get('experiment', f'crossvalidator-{name}')

    run_id = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    logger.info(f'Job run id: {run_id}')
    logger.info(f'Experiment name: {experiment_name}')
    experiment = get_experiment(experiment_name, tags, create_if_not_exists=True)
    trial_name = f'crossvalidator-{name}-{run_id}'
    logger.info(f'Trial name: {trial_name}')
    trial = get_trial(experiment_name, trial_name, tags, create_if_not_exists=True)
    
    # save newly created information to output event
    job_name = get_job_name(name, run_id)
    training_info['TrainingJobName_template'] = get_training_name_template(job_name)
    job_config['job_name'] = job_name
    job_config['run_id'] = run_id
    job_config['experiment_name'] = experiment_name
    job_config['trial_name'] = trial_name
    
    return event
