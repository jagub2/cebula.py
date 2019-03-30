from collections import OrderedDict
import hashlib
import os
import pickle


def sha1sum(string_to_encode: str):
    return hashlib.sha1(string_to_encode.encode('utf-8')).hexdigest()


def sorted_dict(input_dict: dict):
    return dict(OrderedDict(sorted(input_dict.items())))


def get_pickle_dir():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pickles')


def does_pickle_exist(data_hash: str):
    return os.path.exists(os.path.join(get_pickle_dir(), f"{data_hash}.pickle"))


def write_pickle(data_hash: str, object_to_be_pickled):
    try:
        with open(os.path.join(get_pickle_dir(), f"{data_hash}.pickle"), 'wb') as pickle_file:
            pickle.dump(object_to_be_pickled, pickle_file)
    except Exception as e:
        os.unlink(os.path.join(get_pickle_dir(), f"{data_hash}.pickle"))


def load_pickle(data_hash: str):
    with open(os.path.join(get_pickle_dir(), f"{data_hash}.pickle"), 'rb') as pickle_file:
        return pickle.load(pickle_file)
