# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

# TODO: rename paix to reponet (Paix -> RepoNet)
# TODO: make package
# TODO: split up this & its test file
# TODO: complete repo names
# FIXME: starting up with invalid config file causes exception
# TODO: prefix ini section names for repos with "repo:"
# TODO: implicit repos for local directories - both as source and destination!
# TODO: support some pip switches (-r requirements.txt, --pre, --no-use-wheel)
# TODO: support copying all package versions
# FIXME: 'use repo', where repo does not have attributes set causes exception

from cmd import Cmd
import traceback
import abc
import tempfile
import os
import sys
import shutil
import subprocess
from ConfigParser import RawConfigParser
import contextlib
from upload import upload


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
        subprocess.call(cmd)


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


class Repo(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, attributes):
        super(Repo, self).__init__()
        self._attributes = attributes

    def __getattr__(self, key):
        return self._attributes[key]

    @abc.abstractmethod
    def get_as_pip_conf(self):
        pass

    @abc.abstractmethod
    def download_packages(self, package_spec, directory):
        pass

    @abc.abstractmethod
    def upload_packages(self, package_files):
        pass


REPOTYPE_FILE = 'file'
REPOTYPE_HTTP = 'http'
REPOTYPE_PYPI = 'pypi'
REPOTYPE_PIPLOCAL = 'piplocal'


PIPCONF_FILEREPO = '''\
[global]
no-index = true
find-links = {directory}
'''


class FileRepo(Repo):

    def get_as_pip_conf(self):
        return PIPCONF_FILEREPO.format(directory=self.directory)

    def download_packages(self, package_spec, directory):
        pip_install(
            '--find-links', self.directory,
            '--no-index',
            '--download', directory.path,
            package_spec,
        )

    def upload_packages(self, package_files):
        destination = self.directory
        for source in package_files:
            shutil.copy2(source, destination)


class PipLocalRepo(FileRepo):

    @property
    def directory(self):
        return os.path.expanduser('~/.pip/local')


PIPCONF_HTTPREPO = '''\
[global]
index-url = {download_url}
extra-index-url =
'''


class HttpRepo(Repo):

    def get_as_pip_conf(self):
        return PIPCONF_HTTPREPO.format(download_url=self.download_url)

    def download_packages(self, package_spec, directory):
        pip_install(
            '--index-url', self.download_url,
            '--download', directory.path,
            package_spec,
        )

    def upload_packages(self, package_files):
        for source in package_files:
            upload(
                source,
                signature=None,
                repository=self.upload_url,
                username=self.username,
                password=self.password,
                comment='Uploaded with reponet tool',
            )


class PyPIRepo(HttpRepo):

    @property
    def download_url(self):
        return 'https://pypi.python.org/simple'

    @property
    def upload_url(self):
        return 'https://pypi.python.org/'


class UnknownRepoError(NameError):
    '''Repo is not defined at all'''


class UndefinedRepoType(ValueError):
    '''type was not defined for repo'''


class UnknownRepoType(ValueError):
    '''type was given, but it is unknown'''


KEY_TYPE = 'type'
KEY_DIRECTORY = 'directory'
KEY_USERNAME = 'username'
KEY_PASSWORD = 'password'
KEY_DOWNLOAD_URL = 'download_url'
KEY_UPLOAD_URL = 'upload_url'

REPO_ATTRIBUTES = {
    KEY_TYPE,
    KEY_DIRECTORY,
    KEY_DOWNLOAD_URL,
    KEY_UPLOAD_URL,
    KEY_USERNAME,
    KEY_PASSWORD,
}
REPO_ATTRIBUTE_COMPLETIONS = tuple('{}='.format(a) for a in REPO_ATTRIBUTES)

TYPE_TO_CLASS = {
    REPOTYPE_FILE: FileRepo,
    REPOTYPE_PIPLOCAL: PipLocalRepo,
    REPOTYPE_HTTP: HttpRepo,
    REPOTYPE_PYPI: PyPIRepo
}


class RepoManager(object):

    def __init__(self, filename):
        self._repo_store_filename = filename
        self._config = RawConfigParser()
        if os.path.exists(self._repo_store_filename):
            self._config.read(self._repo_store_filename)

    def _save(self):
        with open(self._repo_store_filename, 'wt') as f:
            self._config.write(f)

    def get_repo(self, repo_name):
        if not self._config.has_option(repo_name, KEY_TYPE):
            if self._config.has_section(repo_name):
                raise UndefinedRepoType(repo_name)
            raise UnknownRepoError(repo_name)

        attributes = self.get_attributes(repo_name)
        repo_type = attributes[KEY_TYPE]

        try:
            return TYPE_TO_CLASS[repo_type](attributes)
        except KeyError:
            raise UnknownRepoType(repo_type)

    def define(self, repo_name):
        self._config.add_section(repo_name)
        self._save()

    def forget(self, repo_name):
        self._config.remove_section(repo_name)
        self._save()

    def set(self, repo_name, key, value):
        self._config.set(repo_name, key, value)
        self._save()

    @property
    def repo_names(self):
        return self._config.sections()

    def get_attributes(self, repo_name):
        attributes = {
            option: self._config.get(repo_name, option)
            for option in self._config.options(repo_name)
        }
        return attributes


class BaseCmd(Cmd, object):

    def emptyline(self):
        pass

    def cmdloop(self, intro=None):
        while True:
            try:
                super(BaseCmd, self).cmdloop(intro)
                break
            except Exception:
                traceback.print_exc()
            except KeyboardInterrupt:
                print('^C')
            intro = ''

    def do_EOF(self, line):
        '''
        Exit
        '''
        print('Bye!')
        return True
    do_bye = do_EOF


class Paix(BaseCmd):

    intro = '''
    Paix provides tools to work with different repos of python packages.

    e.g. one might use three different repos:

     - pypi.python.org       (globally shared)
     - private pypi instance (project/company specific,
                              pip needs to be configured to fetch from here)
     - developer cache       (~/.pip/local)
    '''
    prompt = 'Paix: '

    def __init__(self, repo_manager, directory):
        super(Paix, self).__init__()
        self.repo_manager = repo_manager
        self.__temp_dir = directory

    def write_file(self, filename, content):
        write_file(filename, content)

    def do_use(self, repo):
        '''
        Set up pip to use REPO (write ~/.pip/pip.conf)

        use REPO
        '''
        repo = self.repo_manager.get_repo(repo)
        pip_conf = os.path.expanduser('~/.pip/pip.conf')
        self.write_file(pip_conf, repo.get_as_pip_conf())

    def do_copy(self, line):
        '''
        Copy packages between repos

        copy [REPO:]PACKAGE-SPEC [...] REPO:
        '''
        words = line.split()
        destination = words[-1]
        assert destination.endswith(':')
        destination_repo = self.repo_manager.get_repo(destination.rstrip(':'))

        repo = None
        for package_spec in words[:-1]:
            if ':' in package_spec:
                repo_name, _, package_spec = package_spec.partition(':')
                repo = self.repo_manager.get_repo(repo_name)
            if package_spec:
                if not repo:
                    raise AssertionError(
                        'No repo specified for package'.format(package_spec)
                    )
            repo.download_packages(package_spec, self.__temp_dir)

        destination_repo.upload_packages(self.__temp_dir.files)
        self.__temp_dir.clear()

    def do_define(self, repo):
        '''
        Define a new package repository.

        define REPO
        '''
        self.repo_manager.define(repo)

    def do_forget(self, repo):
        '''
        Drop definition of a repo.

        forget REPO
        '''
        self.repo_manager.forget(repo)

    def do_set(self, line):
        '''
        Set repository parameters.

        set repo key=value

        # intended use:
        # file repos:
        set developer-repo type=file
        set developer-repo directory=package-directory

        # http repos:
        set company-private-repo type=http
        set company-private-repo download-url=http://...
        set company-private-repo upload-url=http://...
        set company-private-repo username=user
        set company-private-repo password=pass

        # specials - predefined types:
        set python type=python
        set developer-repo type=piplocal
        '''
        repo, key_value = line.split()
        key, _, value = key_value.partition('=')
        self.repo_manager.set(repo, key, value)

    def complete_set(self, text, line, begidx, endidx):
        completions = ()
        complete_line = line[:endidx]
        words = complete_line.split()
        complete_index = len(words) + (0 if text else 1)
        assert complete_index > 1, "complete on command not done???"
        if complete_index == 2:
            completions = (
                '{} '.format(name) for name in self.repo_manager.repo_names
            )
        elif '=' in words[-1]:
            if words[-1].startswith('type='):
                completions = tuple(TYPE_TO_CLASS)
        else:
            completions = REPO_ATTRIBUTE_COMPLETIONS
        return sorted(c for c in completions if c.startswith(text))

    def do_list(self, line):
        '''
        List known repos
        '''
        repo_names = self.repo_manager.repo_names
        print('Known repos:')
        print('    ' + '\n    '.join(repo_names))

    def do_show(self, repo):
        '''
        List repo attributes - as could be specified in pip.conf
        '''
        attributes = self.repo_manager.get_attributes(repo)
        print(
            '  '
            + '\n  '.join(
                '{}: {}'.format(key, value)
                for key, value in attributes.iteritems()
            )
        )


def main():
    tempdir = tempfile.mkdtemp(suffix='.pypkgs')
    cmd = Paix(
        RepoManager(os.path.expanduser('~/.python.reponet')),
        Directory(tempdir),
    )
    line = ' '.join(sys.argv[1:])
    try:
        if line:
            cmd.onecmd(line)
        else:
            cmd.cmdloop()
    finally:
        shutil.rmtree(tempdir)


if __name__ == '__main__':
    main()
