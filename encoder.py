"""
encoder.py

This file is responsible for providing a new complex encoder object that converts
our project objects into JSON object format.
"""

# Standard library imports
from json import JSONEncoder


class ComplexEncoder(JSONEncoder):
    """
    ComplexEncoder
    """

    def default(self, obj):
        """
        default()

        An overloaded version of the default JSON encode function.

        :params obj: <Object> The object to encode.

        :return: The object encoded as JSON.
        """

        if hasattr(obj, 'to_json'):
            return obj.to_json()
        else:
            return JSONEncoder.default(self, obj)

