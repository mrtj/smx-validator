from builtins import Exception

class InputValidationError(Exception):

    def __init__(self, jsonschema_errors):
        self.jsonschema_errors = jsonschema_errors
        
    def __str__(self):
        msg = 'Error validating input:\n'
        for error in self.jsonschema_errors:
            path = '.'.join(error.path)
            msg += f'    at path {path}: {error.message}\n'
        return msg
