# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import os
from cmd import Cmd
import traceback
from .util import write_file
from .repomanager import RepoManager, FileRepo


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


REPO_ATTRIBUTE_COMPLETIONS = tuple(
    '{}='.format(a)
    for a in RepoManager.REPO_ATTRIBUTES
)


class PyreneCmd(BaseCmd):

    intro = '''
    Pyrene provides tools to work with different repos of python packages.

    e.g. one might use three different repos:

     - pypi.python.org       (globally shared)
     - private pypi instance (project/company specific,
                              pip needs to be configured to fetch from here)
     - developer cache       (~/.pip/local)
    '''
    prompt = 'Pyrene: '

    def __init__(self, repo_manager, directory):
        super(PyreneCmd, self).__init__()
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

    def _get_destination_repo(self, word):
        if word.endswith(':'):
            repo_name = word[:-1]
            return self.repo_manager.get_repo(repo_name)

        attributes = {'directory': word}
        return FileRepo(attributes)

    def do_copy(self, line):
        '''
        Copy packages between repos

        copy [LOCAL-FILE [...]] [REPO:PACKAGE-SPEC [...]] DESTINATION

        The order of parameters is important:
        LOCAL-FILEs should come first if there are any,
        then packages from defined REPOs, then DESTINATION specification.
        DESTINATION can be either a REPO: or a directory.

        '''
        words = line.split()
        destination_repo = self._get_destination_repo(words[-1])

        distribution_files = []
        repo = None
        for word in words[:-1]:
            if ':' in word:
                repo_name, _, package_spec = word.partition(':')
                repo = self.repo_manager.get_repo(repo_name)
            else:
                package_spec = word

            assert ':' not in package_spec

            if package_spec:
                if not repo:
                    distribution_files.append(package_spec)
                else:
                    repo.download_packages(package_spec, self.__temp_dir)

        distribution_files.extend(self.__temp_dir.files)
        destination_repo.upload_packages(distribution_files)
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
                completions = tuple(RepoManager.REPO_TYPES)
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

    def complete_repo_name(self, text, line, begidx, endidx, suffix=''):
        return sorted(
            '{}{}'.format(name, suffix)
            for name in self.repo_manager.repo_names
            if name.startswith(text)
        )
