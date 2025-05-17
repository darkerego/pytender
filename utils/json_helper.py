import json
import time
from os import path


class JsonHelper:
    prefix: str

    def __init__(self, file_name_prefix='configs/vnet_conf'):
        self.prefix = file_name_prefix

    @classmethod
    def load_json(cls, file: str) -> dict:
        assert path.exists(file)
        with open(file, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as err:
                print('[!] Error parsing %s: %s: ' % (file, err))
                return {}

    @classmethod
    def dump_json(cls, obj: dict | list, file: str = None) -> None:
        if not file:
            ts = str(int(time.time()))
            file = '%s_%s' % (cls.prefix, ts)
        with open(file, 'w') as f:
            json.dump(obj, f, indent=4)