import json
from datetime import datetime, date

def json_serial(obj):
    '''JSON serializer for objects not serializable by default json code'''
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f'Type {type(obj)} not serializable')

def clean_json(obj):
    ''' Cleans a json object from datettimes. '''
    return json.loads(json.dumps(obj, default=json_serial))
