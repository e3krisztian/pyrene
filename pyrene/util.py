# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
import shutil
import os
import sys
import subprocess
import signal
import contextlib
from tempfile import NamedTemporaryFile
from passlib.apache import HtpasswdFile
import termcolor
import pipes


def red(text):
    return termcolor.colored(text, 'red')


def green(text):
    return termcolor.colored(text, 'green')


def yellow(text):
    return termcolor.colored(text, 'yellow')


def bold(text):
    return termcolor.colored(text, attrs={'bold'})


def print_command(cmd):
    print(bold(' $ ' + ' '.join(map(pipes.quote, cmd))))


@contextlib.contextmanager
def set_env(variable, value):
    exists = variable in os.environ
    original_value = os.environ.get(variable, '')
    os.environ[variable] = value
    yield
    os.environ[variable] = original_value
    if not exists:
        del os.environ[variable]


def pip_install(*args):
    '''
    Run pip install ...

    Explicitly ignores user's config.
    '''
    pip_cmd = os.path.join(os.path.dirname(sys.executable), 'pip')
    with set_env('PIP_CONFIG_FILE', os.devnull):
        cmd = [pip_cmd, 'install'] + list(args)
        print_command(cmd)
        subprocess.call(cmd, stdout=sys.stdout, stderr=sys.stderr)


class PyPI(object):

    def __init__(self):
        self.directory = '.'
        self.volatile = False
        self.interface = '0.0.0.0'
        self.port = '8080'
        self.users = {}

    def add_user(self, username, password):
        self.users[username] = password

    def make_htpasswd(self, filename):
        ht = HtpasswdFile(path=filename, new=True)
        for username, password in self.users.items():
            ht.set_password(username, password)
        ht.save()

    def serve(self):
        pypi_srv = os.path.join(os.path.dirname(sys.executable), 'pypi-server')
        with NamedTemporaryFile() as password_file:
            self.make_htpasswd(password_file.name)

            cmd = [
                pypi_srv,
                '--interface', self.interface,
                '--port', self.port,
            ] + (
                ['--passwords', password_file.name] if self.users else []
            ) + [
                '--disable-fallback',
            ] + (
                ['--overwrite'] if self.volatile else []
            ) + [self.directory]

            self.execute(cmd)

    def execute(self, cmd):
        print_command(cmd)
        process = subprocess.Popen(cmd)
        try:
            process.wait()
        except KeyboardInterrupt:
            os.kill(process.pid, signal.SIGHUP)
            process.wait()
        print()


def read_file(path, mode='rb'):
    with open(path) as f:
        return f.read()


def write_file(path, content):
    try:
        os.makedirs(os.path.dirname(path))
    except OSError:
        pass
    with open(path, 'wb') as file:
        file.write(content)


def create_md5_backup(filename):
    try:
        with open(filename, 'rb') as f:
            content = f.read()
    except IOError:
        return
    md5 = hashlib.md5(content).hexdigest()
    backup = '{}.{}'.format(filename, md5)
    shutil.copy2(filename, backup)


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


def generate_password():
    import binascii
    return binascii.hexlify(os.urandom(10))
