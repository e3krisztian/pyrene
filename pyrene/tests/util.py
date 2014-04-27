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
    temp = tempfile.SpooledTemporaryFile(mode='w+t')

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


def record_calls(calls, function):
    def recorded(*args, **kwargs):
        calls.append((args, kwargs))
        return function(*args, **kwargs)
    return recorded


def _first_not_found(text, fragments):
    if not fragments:
        return None

    f = fragments[0]
    try:
        pos = text.index(f)
    except ValueError:
        return (text, f)

    return _first_not_found(text[pos + len(f):], fragments[1:])


assert not _first_not_found('abc', ('a', 'b', 'c'))
assert not _first_not_found('abc', ('a', 'c'))
assert not _first_not_found('abc', ('a', 'b'))
assert not _first_not_found('abc', ('b', 'c'))
assert ('c', 'a') == _first_not_found('abc', ('b', 'a'))
assert ('', 'a') == _first_not_found('abc', ('c', 'a'))
assert ('', 'b') == _first_not_found('abc', ('c', 'b', 'a'))

# or the equivalent
assert not _first_not_found('abc', 'abc')
assert not _first_not_found('abc', 'ac')
assert not _first_not_found('abc', 'ab')
assert not _first_not_found('abc', 'bc')
assert ('c', 'a') == _first_not_found('abc', 'ba')
assert ('', 'a') == _first_not_found('abc', 'ca')
assert ('', 'b') == _first_not_found('abc', 'cba')


class Assertions(object):

    def assertContainsInOrder(self, text, fragments):
        mismatch = _first_not_found(text, fragments)
        if mismatch:
            text_part, fragment = mismatch
            skipped = len(text) - len(text_part)
            msg = '\n'.join(
                (
                    '',
                    'Fragment',
                    ' >>> {} <<<'.format(fragment),
                    'not found in text' if not skipped
                    else 'not found in partial text ({} characters skipped)'
                    .format(skipped),
                    ' > ' + text_part.replace('\r', '').replace('\n', '\n > '),
                )
            )
            raise AssertionError(msg)
