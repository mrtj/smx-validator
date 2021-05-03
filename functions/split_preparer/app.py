''' This lambda function customizes / adjusts the hyperparameter template and
other parameters of the current split. Currently it substitutes the following 
template parameters to the appropriate value of the split:
 - `${num_training_samples}` -> the number of the training samples in the split
 - `${num_testing_samples}` -> the number of the testing samples in the split
 - `${fold_name}` -> the name of the fold
'''

import json

def substitute_all(template, substitutions):
    result_str = json.dumps(template)
    for key, value in substitutions.items():
        result_str = result_str.replace(key, str(value))
    result = json.loads(result_str)
    return result

def lambda_handler(event, context):
    training_info = event['training']
    job_config = event['job_config']
    split = event['split']

    split['HyperParameters'] = substitute_all(
        template=training_info['HyperParameters_template'], 
        substitutions={
            '${num_training_samples}': split['num_training_samples'],
            '${num_validation_samples}': split['num_validation_samples'],
            '${num_classes}': split['num_classes']
        }
    )
    del training_info['HyperParameters_template']

    split['TrainingJobName'] = substitute_all(
        template=training_info['TrainingJobName_template'], 
        substitutions={
            '${fold_name}': split['fold_name']
        }
    )
    del training_info['TrainingJobName_template']

    split['tags'] = job_config.get('tags', []).copy()
    split['tags'].extend([
        {
            'Key': 'fold_name',
            'Value': split['fold_name']
        },
        {
            'Key': 'crossvalidator_job_name',
            'Value': job_config['job_name']
        },
        {
            'Key': 'created_by',
            'Value': 'smx-validator'
        }
    ])
    
    return event
