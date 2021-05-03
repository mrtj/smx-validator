'''
This lambda function splits the input dataset into cross-validation folds.
'''

import os
import json
import logging

import s3fs
import numpy as np

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info(f'numpy version: {np.__version__}')
logger.info(f's3fs version: {s3fs.__version__}')

def validate_enum(value, allowed_values, name):
    if not value in allowed_values:
        raise ValueError(f'{name} must be one of {allowed_values}')
    return value

def read_input_lines(s3, input_path):
    logger.info(f'reading from {input_path}')
    with s3.open(input_path) as f:
        lines = f.readlines()
    logger.info(f'read {len(lines)} lines')
    return lines

def write_output_lines(s3, output_path, lines):
    logger.info(f'writing {len(lines)} lines to {output_path}')
    with s3.open(output_path, 'wb') as f:
        f.writelines(lines)

def kfold_split(n_splits, lines, shuffle=True, random_state=42):
    n_samples = len(lines)
    indices = np.arange(n_samples)
    if shuffle:
        rng = np.random.default_rng(random_state)
        rng.shuffle(indices)
    fold_sizes = np.full(n_splits, n_samples // n_splits, dtype=int)
    fold_sizes[:n_samples % n_splits] += 1
    current = 0
    for fold_size in fold_sizes:
        (start, stop) = (current, current + fold_size)
        validation_indices = list(indices[start:stop])
        train_indices = list(indices[:start]) + list(indices[stop:])
        logger.info(f'kfold_split yield train_indices ({len(train_indices)}), validation_indices ({len(validation_indices)})')
        yield train_indices, validation_indices
        current = stop

def split_lines(lines, n_splits, random_state):
    kf = kfold_split(n_splits=n_splits, lines=lines, shuffle=True, random_state=random_state)
    folds = []
    for fold_idx, (train_indices, validation_indices) in enumerate(kf):
        train_lines = [lines[i] for i in train_indices]
        validation_lines = [lines[i] for i in validation_indices]
        logger.info(f'split_lines yield fold_idx: {fold_idx}')
        yield (fold_idx, train_lines, validation_lines)

def count_classes(lines):
    classes = set()
    for line in lines:
        try:
            data = json.loads(line)
            if not 'class' in data:
                return 0
            else:
                classes.add(data['class'])
        except json.decoder.JSONDecodeError:
            return 0
    return len(classes)

def lambda_handler(event, context):
    job_config = event['job_config']
    output_prefix = job_config['output_prefix']
    input_path = job_config['input_path']
    splits_prefix = os.path.join(output_prefix, 'splits')
    crossvalidation_config = event['crossvalidation']
    n_splits = int(crossvalidation_config['n_splits'])
    random_state = crossvalidation_config.get('random_state', 42)
    
    logger.info(f'n splits: {n_splits}')
    logger.info(f'input_path: {input_path}')
    logger.info(f'splits_prefix: {splits_prefix}')
    logger.info(f'random_state: {random_state}')

    s3 = s3fs.S3FileSystem(anon=False)
    lines = read_input_lines(s3, input_path)
    num_lines = len(lines)
    num_classes = count_classes(lines)

    basename_root, basename_ext = os.path.splitext(os.path.basename(input_path))
    make_path = lambda fold_idx, variant: \
        f'{os.path.join(splits_prefix, basename_root)}-fold{fold_idx}-{variant}{basename_ext}'

    splits = []
    for (fold_idx, train_lines, validation_lines) in split_lines(lines, n_splits, random_state=random_state):
        logger.info(f'got fold number: {fold_idx}')
        train_path = make_path(fold_idx, 'train')
        validation_path = make_path(fold_idx, 'validation')
        write_output_lines(s3, train_path, train_lines)
        write_output_lines(s3, validation_path, validation_lines)
        splits.append({
            'train': train_path,
            'validation': validation_path,
            'fold_name': f'fold{fold_idx}',
            'num_training_samples': str(len(train_lines)),
            'num_validation_samples': str(len(validation_lines)),
            'num_classes': str(num_classes)
        })

    event['splits'] = splits
    logger.info('Returning event:')
    logger.info(json.dumps(event))
    return event
