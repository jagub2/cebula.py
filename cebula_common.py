from collections import OrderedDict
import hashlib
import os
import pickle
import redis
import threading
import traceback
import unidecode


class IdList:

    def __init__(self, config: dict):
        self.redis = redis.Redis(**config)

    def is_id_present(self, id_):
        lock = threading.Lock()
        with lock:
            return id_.encode('utf-8') in self.redis.smembers('cebulapy_cache')
        return False

    def put_ids(self, ids):
        lock = threading.Lock()
        with lock:
            if len(ids) > 0:
                self.redis.sadd('cebulapy_cache', *ids)

    def __getstate__(self):
        state_dict = self.__dict__.copy()
        del state_dict['redis']
        return state_dict


def sha1sum(string_to_encode: str) -> str:
    return hashlib.sha1(string_to_encode.encode('utf-8')).hexdigest()


def sorted_dict(input_dict: dict) -> dict:
    return dict(OrderedDict(sorted(input_dict.items())))


def get_pickle_dir() -> str:
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pickles')


def does_pickle_exist(data_hash: str, class_name: str) -> bool:
    return os.path.exists(os.path.join(get_pickle_dir(), f"{class_name}-{data_hash}.pickle"))


def write_pickle(data_hash: str, object_to_be_pickled):
    try:
        with open(os.path.join(get_pickle_dir(), f"{object_to_be_pickled.__class__.__name__}-{data_hash}.pickle"), 'wb') as pickle_file:
            pickle.dump(object_to_be_pickled, pickle_file)
    except Exception as e:
        print(f"cebula_common: Got exception: {e}")
        os.unlink(os.path.join(get_pickle_dir(), f"{object_to_be_pickled.__class__.__name__}-{data_hash}.pickle"))
        traceback.print_stack()


def load_pickle(data_hash: str, class_name: str):
    with open(os.path.join(get_pickle_dir(), f"{class_name}-{data_hash}.pickle"), 'rb') as pickle_file:
        return pickle.load(pickle_file)


def remove_accents(input_string: str) -> str:
    return unidecode.unidecode(input_string)
