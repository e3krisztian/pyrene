# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import subprocess
import signal
import contextlib
from tempfile import NamedTemporaryFile
from passlib.apache import HtpasswdFile


@contextlib.contextmanager
def set_env(key, value):
    exists = key in os.environ
    original_value = os.environ.get(key, '')
    os.environ[key] = value
    yield
    os.environ[key] = original_value
    if not exists:
        del os.environ[key]


def pip_install(*args):
    '''
    Run pip install ...

    Explicitly ignores user's config.
    '''
    pip_cmd = os.path.join(os.path.dirname(sys.executable), 'pip')
    with set_env('PIP_CONFIG_FILE', os.devnull):
        cmd = [pip_cmd, 'install'] + list(args)
        print(' '.join(cmd))
        subprocess.call(cmd, stdout=sys.stdout, stderr=sys.stderr)


def make_htpasswd(filename, username, password):
    ht = HtpasswdFile(path=filename, new=True)
    ht.set_password(username, password)
    ht.save()


def pypi_server(
    directory,
    username,
    password,
    interface='0.0.0.0',  # all interfaces
    port='8080',
    volatile=False,       # allow package overwrites?
):
    '''
    Run pypi-server.
    '''
    pypi_srv = os.path.join(os.path.dirname(sys.executable), 'pypi-server')
    with NamedTemporaryFile() as password_file:
        make_htpasswd(password_file.name, username, password)

        cmd = [
            pypi_srv,
            '--interface', interface,
            '--port', port,
            '--passwords', password_file.name,
            '--disable-fallback',
        ] + (
            ['--overwrite'] if volatile else []
        ) + [directory]

        process = subprocess.Popen(cmd)
        try:
            process.wait()
        except KeyboardInterrupt:
            os.kill(process.pid, signal.SIGHUP)
            process.wait()
        print()


def write_file(path, content):
    try:
        os.makedirs(os.path.dirname(path))
    except OSError:
        pass
    with open(path, 'wb') as file:
        file.write(content)


class Directory(object):

    def __init__(self, path):
        self.path = os.path.normpath(path)

    @property
    def files(self):
        candidates = (
            os.path.join(self.path, f) for f in os.listdir(self.path)
        )
        return sorted(f for f in candidates if os.path.isfile(f))

    def clear(self):
        for path in self.files:
            os.remove(path)
