import glob
import json
import os


def load_routes(directory_path='routes'):
    for filename in glob.glob('*.json', root_dir=directory_path):
        filepath = os.path.join(directory_path, filename)
        with open(filepath, 'r', encoding='utf8') as file:
            yield json.load(file)
