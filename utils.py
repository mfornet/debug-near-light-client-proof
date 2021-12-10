import os
import json
from dotmap import DotMap

TARGET_FOLDER = 'memo'


def memo(func):
    def func_memo(*args):
        target_folder = os.path.join(TARGET_FOLDER, func.__name__)
        os.makedirs(target_folder, exist_ok=True)
        target_file = os.path.join(target_folder, '-'.join(map(str, args)))

        if os.path.exists(target_file):
            with open(target_file, 'r') as f:
                return DotMap(json.load(f))

        result = func(*args)

        with open(target_file, 'w') as f:
            json.dump(result, f, indent=2)

        return result

    return func_memo
