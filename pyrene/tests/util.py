import tempfile
import sys
import contextlib


class External(object):
    def __init__(self, temp):
        self.temp = temp

    def getvalue(self):
        return self.content

    @property
    def content(self):
        self.temp.file.flush()
        with open(self.temp.name, 'rb') as f:
            return f.read()


@contextlib.contextmanager
def capture_stdout():
    orig = sys.stdout
    temp = tempfile.NamedTemporaryFile()

    with temp:
        sys.stdout = temp.file
        yield External(temp)
        sys.stdout = orig
