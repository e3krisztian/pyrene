import tempfile
import sys
import contextlib
from io import StringIO


class External(object):
    # TODO: use real external
    def __init__(self, file):
        self._file = file

    def getvalue(self):
        return self.content

    @property
    def content(self):
        self._file.seek(0)
        return self._file.read()


@contextlib.contextmanager
def capture_stdout():
    orig = sys.stdout
    temp = tempfile.SpooledTemporaryFile()

    with temp:
        sys.stdout = temp
        yield External(temp)
        sys.stdout = orig


@contextlib.contextmanager
def fake_stdin(text):
    stdin = sys.stdin
    sys.stdin = StringIO(text)
    yield
    sys.stdin = stdin
