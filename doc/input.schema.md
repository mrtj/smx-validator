# SageMaker Cross-validator state machine input

*The input of the SageMaker Cross-validator state machine.*

## Properties

- **`job_config`** *(object)*: This section defines parameters that are global for the cross-validated training job. Cannot contain additional properties.

  Examples:
  ```json
  {
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
  }
  ```
  - **`name`** *(string)*: An identifying name of the training job. Will be suffixed with the current timestamp to generate the names of the SageMaker training jobs.
  - **`input_path`** *(string)*: The S3 URL of the input text file. This text file will be sliced into cross-validated folds that will be fed to the training container. The bucket in this path should match the `InputBucketName` CloudFormation parameter.
  - **`output_prefix`** *(string)*: Cross-validation fold inputs as well as all trained models will be written under this S3 URL prefix. The bucket in the prefix should match the `OutputBucketName` CloudFormation parameter.
  - **`experiment`** *(string)*: The name of the SageMaker Experiment that will be used to track the hyperparameters and the metrics of the training jobs. If the experiment is not existing yet, it will be created.
  - **`tags`** *(array)*: All tags defined in this section will be propageted to the SageMaker training jobs created by the cross-validator.
    - **Items** *(object)*: AWS API style tag entry. Cannot contain additional properties.
      - **`Key`** *(string)*: The Key of the tag.
      - **`Value`** *(string)*: The Value of the tag.
- **`crossvalidation`** *(object)*: This section defines parameters regarding the k-fold cross-validation dataset generation. Cannot contain additional properties.

  Examples:
  ```json
  {
      "n_splits": 5,
      "random_state": 42
  }
  ```
  - **`n_splits`** *(integer)*: The number of k-fold splits to be generated. It is also equal to the number of training jobs that will be launched. Minimum: `2`. Default: `5`.
  - **`random_state`** *(integer)*: The initial state (seed) of the random number generator used to generate the cross-validated splits. Specifying the same number and the same input file will generate the same splits. Minimum: `0`. Default: `42`.
- **`training`** *(object)*: This section provides a template for the SageMaker training job parameters. Most of these parameters will be directly mapped to the appropiate fields of the SageMaker [CreateTrainingJob](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_CreateTrainingJob.html) API request. Cannot contain additional properties.

  Examples:
  ```json
  {
      "hyperparameters_template": {
          "num_classes": "${num_classes}",
          "learning_rate": "0.0005"
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
  ```
  - **`hyperparameters_template`** *(object)*: Hyperparameters to be passed to the SageMaker training job. A simple template substitution will be performed in order to set split-specific hyperparameters. All hyperparameters, including numeric and bool types should be converted to string. Can contain additional properties.

    Examples:
    ```json
    {
        "num_classes": "${num_classes}",
        "num_training_samples": "${num_training_samples}",
        "string_hyperparam": "foo",
        "numeric_hyperparam": "42",
        "boolean_hyperparam": "true"
    }
    ```
  - **`algorithm_specification`** *(object)*: The algorithm specification of the SageMaker training jobs. This section will be directly mapped to the [AlgorithmSpecification](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_AlgorithmSpecification.html) field of the CreateTrainingJob request. Can contain additional properties.

    Examples:
    ```json
    {
        "TrainingImage": "685385470294.dkr.ecr.eu-west-1.amazonaws.com/image-classification:1",
        "TrainingInputMode": "Pipe"
    }
    ```
  - **`stopping_condition`** *(object)*: The stopping condition of the SageMaker training jobs. This section will be directly mapped to the [StoppingCondition](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_StoppingCondition.html) field of the CreateTrainingJob request. Can contain additional properties.

    Examples:
    ```json
    {
        "MaxRuntimeInSeconds": 3600,
        "MaxWaitTimeInSeconds": 7200
    }
    ```
  - **`resource_config`** *(object)*: The resource configuraiton of the SageMaker training jobs. This section will be directly mapped to the [ResourceConfig](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ResourceConfig.html) field of the CreateTrainingJob request. Can contain additional properties.

    Examples:
    ```json
    {
        "InstanceCount": 1,
        "InstanceType": "ml.p3.2xlarge",
        "VolumeSizeInGB": 10
    }
    ```

*Generated by https://github.com/mrtj/jsonschema2md*
