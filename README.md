# SMX-Validator

> Orchestrate k-fold cross validated training jobs on Amazon Web Services infrastructure.

## Introduction

This application orchestrates [k-fold cross-validated training](https://en.wikipedia.org/wiki/Cross-validation_(statistics)#k-fold_cross-validation) of machine learning models with [AWS SageMaker](https://docs.aws.amazon.com/sagemaker/latest/dg/how-it-works-training.html). You can use any supervised training container that accepts a newline separated file as input, for example:
 - Linear Learner with [CSV input format](https://docs.aws.amazon.com/sagemaker/latest/dg/linear-learner.html#ll-input_output)
 - K-Nearest Neighbors Algorithm with [CSV input format](https://docs.aws.amazon.com/sagemaker/latest/dg/k-nearest-neighbors.html#kNN-input_output)
 - Image Classification Algorithm with [Augmented Manifest Image Format](https://docs.aws.amazon.com/sagemaker/latest/dg/image-classification.html#IC-augmented-manifest-training)
 - XGBoost Algorithm with [CSV input format](https://docs.aws.amazon.com/sagemaker/latest/dg/xgboost.html#InputOutput-XGBoost)
 - BlazingText in Text Classification mode with [File Mode or Augmented Manifest Text Format](https://docs.aws.amazon.com/sagemaker/latest/dg/blazingtext.html#blazingtext-data-formats-text-class)
 - your custom training container that accepts newline separated files as input.

When you create a cross-validated training job, you specify your whole dataset as input. SMX-Validator will take to split the dataset into cross-validated folds and launch a training job for each fold. The specific training container and hyperparameters you can set as the [input](#input-schema) of the cross-validated training job.

SMX-Validator uses [AWS Step Functions](https://aws.amazon.com/step-functions/) to coordinate the training of the cross-validated folds on the available resources. AWS Step Functions lets you coordinate multiple AWS services into serverless workflows.

All SageMaker training jobs launched by the cross-validator will be organized under [SageMaker Experiments](https://docs.aws.amazon.com/sagemaker/latest/dg/experiments.html) so you can easily review the resulting metrics. You can also set your custom tags to the training jobs.

## Deploying SMX-Validator

This repository contains a [Serverless Application Model](https://aws.amazon.com/serverless/sam/) (SAM) project. Clone this repo into your workstation, set up your AWS credentials and install the SAM Command Line Interface.

The Serverless Application Model Command Line Interface (SAM CLI) is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run your functions in an Amazon Linux environment that matches Lambda.

To use the SAM CLI, you need the following tools:

* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3 installed](https://www.python.org/downloads/)
* Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

To build and deploy your application for the first time, run the following in your shell:

```bash
sam build --use-container
sam deploy --guided
```

The first command will build the source of your application. The second command will package and deploy your application to AWS, with a series of prompts:

* **Stack Name**: The name of the stack to deploy to CloudFormation. This should be unique to your account and region, and a good starting point would be something matching your project name (SMX-Validator).
* **AWS Region**: The AWS region you want to deploy your app to.
* **Parameter InputBucketName**: The name of the input bucket. Deploying this application will create an IAM role that allows reading files from this bucket. The input text file should be placed in this bucket.
* **Parameter OutputBucketName**: The name of the output bucket. Deploying this application will create an IAM role that allows writing files in this bucket. The cross-validated training and validation inputs and the training results will be written to this bucket.
* **Confirm changes before deploy**: If set to yes, any change sets will be shown to you before execution for manual review. If set to no, the AWS SAM CLI will automatically deploy application changes.
* **Allow SAM CLI IAM role creation**: Many AWS SAM templates, including this example, create AWS IAM roles required for the AWS Lambda function(s) included to access AWS services. By default, these are scoped down to minimum required permissions. To deploy an AWS CloudFormation stack which creates or modifies IAM roles, the `CAPABILITY_IAM` value for `capabilities` must be provided. If permission isn't provided through this prompt, to deploy this example you must explicitly pass `--capabilities CAPABILITY_IAM` to the `sam deploy` command.
* **Save arguments to samconfig.toml**: If set to yes, your choices will be saved to a configuration file inside the project, so that in the future you can just re-run `sam deploy` without parameters to deploy changes to your application.

After the deployment of the CloudFormation stack note the value of the `CrossValidatorStateMachineArn` output parameter: you will need it when launching a new cross-validated training job.

### Cleanup

To delete the deployed SMX-Validator application, use the AWS CLI. Assuming you used your project name for the stack name, you can run the following:

```bash
aws cloudformation delete-stack --stack-name sagemaker-crossvalidator
```

## Usage

SMX-Validator deploys a Step Functions state machine that orchestrates the training of the cross-validated folds. You can start a cross-validated job launching a new execution of the state machine. You should specify the [input parameters](#input-schema) of the cross-validated training job in a json file. 

You have different options to start the execution of the state machine:

1. Using the the [AWS CLI](https://docs.aws.amazon.com/cli/latest/reference/stepfunctions/start-execution.html):
    ```bash
    aws stepfunctions start-execution \
        --state-machine-arn {CrossValidatorStateMachineArn} \
        --input file://my_input.json
    ```
2. From the [AWS Step Functions web console](https://console.aws.amazon.com/states/home#/statemachines) select the `CrossValidatorStateMachine-*` and on the state machine page click the "Start execution" button. Copy the contents of your input json into the Input text area.

3. Using the [AWS SDKs](https://aws.amazon.com/tools/), from a local script or from a lambda function.

### Training jobs

SMX-Validator will launch a SageMaker training job for each cross-validated splits. The number of splits you define in the `crossvalidation.n_splits` parameter. The training jobs will be named based on the following template:

```
crossvalidator-{job_config.name}-{YYYYMMDD}-{HHMMSS}-fold{fold_idx}
```

where `job_config.name` is the job name from the input configuration, `{YYYYMMDD}-{HHMMSS}` is the timestamp of the time at the start job and `fold_idx` is the zero-based index of the fold. The jobs are tagged with the tags specified in the `job_config.tags` parameter and registered in the `job_config.experiment` named SageMaker Experiment.

### Hyperparameters

You can pass all hyperparameters of the training job in the `training.hyperparameter_template` input parameter. A simply template substitution will be performed in order to set split-specific hyperparameters required by some SageMaker algorithm. Namely the following strings will be substituted to the appropriate values:

 - `${num_training_samples}`: the number of training samples in the current split
 - `${num_validation_samples}`: the number of validation samples in the current split
 - `${num_classes}`: the number of classes if this is a classification task with json lines augmented manifest format input containing the `class` fields.

Pay attention to convert _all_ hyperparameters to `string` type as the underlying SageMaker training jobs expect so. Example:

```json
{
    "training": {
        "hyperparameter_template": {
            "num_classes": "${num_classes}",
            "num_training_samples": "${num_training_samples}",
            "string_hyperparam": "foo",
            "numeric_hyperparam": "42",
            "boolean_hyperparam": "true"
        }
    }
}
```

### Input schema

You should specify a well defined json file as an input of the state machine execution. You can find below the expected format of the input. For a complete reference of the input format refer directly to the [input schema specification](resources/schemas/input.schema.json), the [input schema documentation](doc/input.schema.md) or a [complete example](doc/sample_event.json) also shown bellow:

```json
{
    "job_config": {
        "output_prefix": "s3://bucket/output_prefix",
        "input_path": "s3://bucket/path/input.jsonl",
        "name": "my_training",
        "experiment": "my_training_experiment",
        "tags": [
            { 
                "Key": "project",
                "Value": "my_project"
            }
        ]
    },
    "crossvalidation": {
        "n_splits": 5,
        "random_state": 42
    },
    "training": {
        "hyperparameters_template": {
            "num_classes": "${num_classes}",
            "num_training_samples": "${num_training_samples}",
            "foo": "bar"
        },
        "algorithm_specification": {
            "TrainingImage": "685385470294.dkr.ecr.eu-west-1.amazonaws.com/image-classification:1",
            "TrainingInputMode": "Pipe"
        },
        "stopping_condition": {
            "MaxRuntimeInSeconds": 3600,
            "MaxWaitTimeInSeconds": 7200
        },
        "resource_config": {
            "InstanceCount": 1,
            "InstanceType": "ml.p3.2xlarge",
            "VolumeSizeInGB": 10
        }
    }
}
```

## Project structure

This project contains source code and supporting files for a serverless application that you can deploy with the SAM CLI. It includes the following files and folders:

- `functions` - Code for the application's Lambda functions to manage the cross-validated SageMaker training jobs
- `statemachines` - Definition for the state machine that orchestrates the cross-validated trainings
- `template.yaml` - A template that defines the application's AWS resources.

The application uses several AWS resources, including Step Functions state machines and Lambda functions. These resources are defined in the `template.yaml` file in this project. 

AWS Step Functions lets you coordinate multiple AWS services into serverless workflows so you can build and update apps quickly. Using Step Functions, you can design and run workflows that stitch together services, such as AWS Lambda, AWS Fargate, and Amazon SageMaker, into feature-rich applications.
