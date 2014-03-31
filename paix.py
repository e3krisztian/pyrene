# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals


from cmd import Cmd
import traceback
import abc


class Directory(object):

    @property
    def files(self):
        # TODO
        pass


class Repo(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def save_as_pip_conf(self):
        # TODO
        pass

    @abc.abstractmethod
    def download_packages(self, package_spec, directory):
        # TODO
        pass

    @abc.abstractmethod
    def upload_packages(self, package_files):
        # TODO
        pass


class RepoManager(object):

    def get_repo(self):
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
        self.repo_manager = repo_manager
        self.__directory = directory

    def do_use(self, repo):
        '''
        Set up pip to use REPO
        '''
        repo = self.repo_manager.get_repo(repo)
        repo.save_as_pip_conf()

    def do_copy(self, line):
        '''
        copy [REPO:]PACKAGE-SPEC [...] REPO:
        '''
        repo = None
        words = line.split()
        destination = words[-1]
        assert destination.endswith(':')
        destination_repo = self.repo_manager.get_repo(destination.rstrip(':'))
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
