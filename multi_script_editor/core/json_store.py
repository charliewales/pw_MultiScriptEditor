import codecs
import json
import os
import tempfile
from contextlib import contextmanager

from vendor.Qt.QtCore import QLockFile


@contextmanager
def locked_json(path):
    lock = QLockFile(path + '.lock')
    if not lock.tryLock(5000):
        raise OSError('Could not lock settings file: {0}'.format(path))
    try:
        yield
    finally:
        lock.unlock()


def write_json(path, data):
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)
    descriptor, temporary_path = tempfile.mkstemp(
        suffix='.tmp',
        dir=folder or None,
    )
    os.close(descriptor)
    try:
        with codecs.open(temporary_path, 'w', 'utf-16') as stream:
            json.dump(data, stream, indent=4)
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)
