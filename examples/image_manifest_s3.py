import sys
import boto3

client = boto3.client('s3')

def warning(msg):
    print('Warning: {}'.format(msg), file=sys.stderr)

def write_entry(f, path, label):
    f.write('{{"source-ref":"{}", "class":"{}"}}\n'.format(path, label))

def manifest_s3(bucket, prefix, labels, output):
    paginator = client.get_paginator('list_objects')
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)
    def do_write(f):
        for page in page_iterator:
            for obj in page['Contents']:
                key = obj['Key']
                label_found = False
                for idx, label in enumerate(label_list):
                    if label in key:
                        if label_found:
                            warning('multiple labels for {}'.format(key))
                        write_entry(f, 's3://{}/{}'.format(bucket, key), idx)
                        label_found = True
                if not label_found:
                    warning('could not find label for {}'.format(key))
    if output == '-':
        do_write(sys.stdout)
    else:
        with open(output, 'w') as f:
            do_write(f)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Creates Augmented Manifest Image Format from files in a S3 bucket.',
        epilog='Example: {} my_bucket datasets/dogs-vs-cats dog.,cat.'.format(sys.argv[0]))
    parser.add_argument('bucket', type=str, help='S3 bucket name')
    parser.add_argument('prefix', type=str, help='S3 prefix')
    parser.add_argument('labels', type=str, help='Comma-separated list of class names')
    parser.add_argument('-o', '--output', help='Output file name', default='-')
    args = parser.parse_args()
    label_list = args.labels.split(',')
    manifest_s3(args.bucket, args.prefix, label_list, args.output)
