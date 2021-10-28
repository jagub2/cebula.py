from collections import OrderedDict
from loguru import logger
import hashlib
import os
import pickle
import redis
import threading
import traceback
import unidecode


class IdList:

    def __init__(self, config: dict):
        self.config = config
        self.redis = redis.Redis(**self.config)
        self.lock = threading.Lock()

    def is_id_present(self, id_):
        with self.lock:
            return self.redis.sismember('cebulapy_cache', id_)
        return False

    def put_ids(self, ids):
        with self.lock:
            if len(ids) > 0:
                self.redis.sadd('cebulapy_cache', *ids)

    def __getstate__(self):
        state_dict = self.__dict__.copy()
        del state_dict['redis']
        del state_dict['lock']
        return state_dict

    def __setstate(self, state_dict):
        state_dict['lock'] = threading.Lock()
        state_dict['redis'] = redis.Redis(**state_dict['config'])
        self.__dict__ = state_dict


def sha1sum(string_to_encode: str) -> str:
    return hashlib.sha1(string_to_encode.encode('utf-8')).hexdigest()


def sorted_dict(input_dict: dict) -> dict:
    dict_ = input_dict.copy()
    if 'randomize_user_agent' in dict_ and 'user_agent' in dict_:
        del dict_['user_agent']
    return dict(OrderedDict(sorted(dict_.items())))


def get_pickle_dir() -> str:
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pickles')


def does_pickle_exist(data_hash: str, class_name: str) -> bool:
    return os.path.exists(os.path.join(get_pickle_dir(), f"{class_name}-{data_hash}.pickle"))


def write_pickle(data_hash: str, object_to_be_pickled):
    try:
        with open(os.path.join(get_pickle_dir(), f"{object_to_be_pickled.__class__.__name__}-{data_hash}.pickle"), 'wb') as pickle_file:
            pickle.dump(object_to_be_pickled, pickle_file)
    except Exception as e:
        logger.error(f"cebula_common: Got exception: {e}")
        os.unlink(os.path.join(get_pickle_dir(), f"{object_to_be_pickled.__class__.__name__}-{data_hash}.pickle"))
        traceback.print_stack()


def load_pickle(data_hash: str, class_name: str):
    with open(os.path.join(get_pickle_dir(), f"{class_name}-{data_hash}.pickle"), 'rb') as pickle_file:
        return pickle.load(pickle_file)


def remove_accents(input_string: str) -> str:
    return unidecode.unidecode(input_string)

def for_all_methods(decorator):
    def decorate(cls):
        for attr in cls.__dict__: # there's propably a better way to do this
            if callable(getattr(cls, attr)):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate
