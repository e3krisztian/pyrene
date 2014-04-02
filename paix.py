# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals


from cmd import Cmd
import traceback
import abc

import pip
import os
import shutil
from ConfigParser import RawConfigParser
import contextlib


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
    with set_env('PIP_CONFIG_FILE', os.devnull):
        return pip.main(['install'] + list(args))


def twine_upload(filename, upload_url, username, password):
    # TODO
    pass


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
        return sorted(
            f for f in os.listdir(self.path)
            if os.path.isfile(os.path.join(self.path, f))
        )


class Repo(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, attributes):
        super(Repo, self).__init__()
        self._attributes = attributes

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
REPOTYPE_PYPI = 'PyPI'
REPOTYPE_PIPLOCAL = 'piplocal'


PIPCONF_FILEREPO = '''\
[global]
no-index = true
find-links = {directory}
'''


class FileRepo(Repo):

    @property
    def directory(self):
        return self._attributes[KEY_DIRECTORY]

    def get_as_pip_conf(self):
        return PIPCONF_FILEREPO.format(directory=self.directory)

    def download_packages(self, package_spec, directory):
        pip_install(
            [
                '--find-links', self.directory,
                '--no-index',
                '--download', directory.path,
                package_spec,
            ]
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
process-dependency-links = false
'''


class HttpRepo(Repo):

    @property
    def username(self):
        return self[KEY_USERNAME]

    @property
    def password(self):
        return self[KEY_PASSWORD]

    @property
    def download_url(self):
        return self[KEY_DOWNLOAD_URL]

    @property
    def upload_url(self):
        return self[KEY_UPLOAD_URL]

    def get_as_pip_conf(self):
        return PIPCONF_HTTPREPO.format(download_url=self.download_url)

    def download_packages(self, package_spec, directory):
        pip_install(
            [
                '--index-url', self.download_url,
                '--download', directory.path,
                package_spec,
            ]
        )

    def upload_packages(self, package_files):
        for source in package_files:
            twine_upload(source, self.upload_url, self.username, self.password)


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

        repo_type = self._config.get(repo_name, KEY_TYPE)

        attributes = {
            option: self._config.get(repo_name, option)
            for option in self._config.options(repo_name)
        }

        try:
            return TYPE_TO_CLASS[repo_type](attributes)
        except KeyError:
            raise UnknownRepoType(repo_type)

    def define(self, repo_name):
        self._config.add_section(repo_name)
        self._save()

    def drop(self, repo_name):
        self._config.remove_section(repo_name)
        self._save()

    def set(self, repo_name, key, value):
        self._config.set(repo_name, key, value)
        self._save()


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
        self.__directory = directory

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
            repo.download_packages(package_spec, self.__directory)

        destination_repo.upload_packages(self.__directory.files)

    def do_define(self, repo):
        '''
        Define a new package repository.

        define REPO
        '''
        self.repo_manager.define(repo)

    def do_drop(self, repo):
        '''
        Drop definition of a repo.

        drop REPO
        '''
        self.repo_manager.drop(repo)

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
