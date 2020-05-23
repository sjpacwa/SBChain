import json


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'to_json'):
            return obj.to_json()
        else:
            return json.JSONEncoder.default(self, obj)


class ComplexDecoder(json.JSONDecoder):
    def default(self, obj):
        if hasattr(obj, 'to_string'):
            return obj.to_string()
        else:
            return json.JSONDecoder.default(self, obj)
