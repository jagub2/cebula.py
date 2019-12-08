from collections import OrderedDict
import hashlib
import os
import pickle
import traceback
import unidecode


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
        os.unlink(os.path.join(get_pickle_dir(), f"{object_to_be_pickled.__class__.__name__}-{data_hash}.pickle"))
        traceback.print_stack()


def load_pickle(data_hash: str, class_name: str):
    with open(os.path.join(get_pickle_dir(), f"{class_name}-{data_hash}.pickle"), 'rb') as pickle_file:
        return pickle.load(pickle_file)


def remove_accents(input_string: str) -> str:
    return unidecode.unidecode(input_string)
