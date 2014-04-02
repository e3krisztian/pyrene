# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals


from cmd import Cmd
import traceback
import abc

import pip
import os
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
    # FIXME: UNTESTED
    with set_env('PIP_CONFIG_FILE', os.devnull):
        return pip.main(['install'] + args)


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

    @abc.abstractmethod
    def get_as_pip_conf(self):
        pass

    @abc.abstractmethod
    def download_packages(self, package_spec, directory):
        pass

    @abc.abstractmethod
    def upload_packages(self, package_files):
        pass


# TODO:
# concrete implementations:
# class FileRepo
# class HttpRepo
# class PythonRepo(HttpRepo)


class RepoManager(object):

    def get_repo(self):
        # TODO
        pass

    def define(self):
        # TODO
        pass

    def drop(self, repo):
        # TODO
        pass

    def set(self, repo, key, value):
        # TODO
        pass


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
        # TODO
        pass

    def do_use(self, repo):
        '''
        Set up pip to use REPO (write ~/.pip/pip.conf)

        use REPO
        '''
        repo = self.repo_manager.get_repo(repo)
        self.write_file('~/.pip/pip.conf', repo.get_as_pip_conf())

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
