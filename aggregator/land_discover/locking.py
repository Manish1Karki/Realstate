from contextlib import contextmanager
from .db import db_path

@contextmanager
def single_job(name):
    """OS lock released on crash; serializes CLI batches on Windows and Unix."""
    path=db_path().parent/(name+'.lock'); path.parent.mkdir(parents=True,exist_ok=True)
    f=open(path,'a+b'); f.write(b'0'); f.flush(); f.seek(0)
    import os
    try:
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError:
        f.close(); raise RuntimeError(f'Another {name} process is running')
    try: yield
    finally:
        f.seek(0)
        if os.name=='nt': msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
        else: fcntl.flock(f,fcntl.LOCK_UN)
        f.close()
