# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals


from cmd import Cmd
import os.path
import shutil
# from temp_dir import within_temp_dir
import traceback


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


class Executor(object):

    def copy(self, source, destination):
        try:
            os.makedirs(os.path.dirname(destination))
        except OSError:
            pass
        shutil.copy2(
            os.path.expanduser(source),
            os.path.expanduser(destination)
        )


class Paix(BaseCmd):

    intro = '''
    Paix provides tools to work with different repos of python packages:

     - pypi.python.org       (globally shared)
     - private pypi instance (project/company specific,
                              pip needs to be configured to fetch from here)
     - developer cache       (~/.pip/local)
    '''
    prompt = 'Paix: '

    def __init__(self, executor):
        self.__executor = executor

    def do_use(self, repo):
        '''
        Set up pip to use REPO
        '''
        self.__executor.copy(
            '~/.paix/repos/{}/pip.conf'.format(repo),
            '~/.pip/pip.conf'
        )

    def do_copy(self, line):
        '''
        copy [REPO:]PACKAGE-SPEC [...] REPO:
        '''
        # words = line.replace(':', ': ').split()
        # check
        # destination_repo = words[-1]
