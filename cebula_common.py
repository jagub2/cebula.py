import hashlib


def sha1sum(string_to_encode: str):
    return hashlib.sha1(string_to_encode.encode('utf-8')).hexdigest()
