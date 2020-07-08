from finance.settings import SECRET_KEY
from hashids import Hashids


HASHIDS = Hashids(salt=SECRET_KEY, min_length=4)

def generate_filename(filename):
    '''
    自定义上传文件的的文件名
    '''
    import os
    import time
    import random
    dirname, filename = os.path.split(filename)
    ext = os.path.splitext(filename)[1]
    new_name = '%d%d%s' % (int(time.time()), random.randint(0, 100), ext)
    return os.path.normpath(os.path.join(dirname, new_name))