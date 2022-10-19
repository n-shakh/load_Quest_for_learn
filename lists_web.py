import json
from config import settings

from alias_types import PathJsonFile, DictIdJsonFile


def flist_web(file: PathJsonFile = settings.list_id) -> DictIdJsonFile:
    with open(file, 'r') as f:
        return json.load(f)


list_web = flist_web()
