# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import os
from cmd import Cmd
import traceback
from .util import write_file
from .repomanager import RepoManager, DirectoryRepo
from pyrene import repomanager


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

    def do_write_pip_conf_for(self, repo):
        '''
        Set up pip to use REPO by default (write ~/.pip/pip.conf)

        write_pip_conf_for REPO
        '''
        repo = self.repo_manager.get_repo(repo)
        pip_conf = os.path.expanduser('~/.pip/pip.conf')
        self.write_file(pip_conf, repo.get_as_pip_conf())

    def _get_destination_repo(self, word):
        if word.endswith(':'):
            repo_name = word[:-1]
            return self.repo_manager.get_repo(repo_name)

        attributes = {'directory': word}
        return DirectoryRepo(attributes)

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

        # directory repos:
        set developer-repo type=directory
        set developer-repo directory=package-directory

        # http repos:
        set company-private-repo type=http
        set company-private-repo download-url=http://...
        set company-private-repo upload-url=http://...
        set company-private-repo username=user
        set company-private-repo password=pass
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
            completions = self.complete_repo_name(
                text, line, begidx, endidx, suffix=' '
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

    complete_forget = complete_repo_name
    complete_show = complete_repo_name
    complete_write_pip_conf_for = complete_repo_name

    def complete_filenames(self, text, line, begidx, endidx):
        dir_prefix = '.'

        line_before = line[:begidx]
        if not line_before.endswith(' '):
            words = line_before.split()
            if len(words) > 1:
                dir_prefix = os.path.dirname(words[-1]) or '.'

        dir_prefix = os.path.abspath(dir_prefix)

        return sorted(
            (f + '/') if os.path.isdir(os.path.join(dir_prefix, f)) else f
            for f in os.listdir(dir_prefix)
            if f.startswith(text)
        )

    def complete_copy(self, text, line, begidx, endidx):
        line_before = line[:begidx]

        if line_before.endswith(':'):
            # no completion after "repo:"
            return []

        repos = []

        if line_before.endswith(' '):
            repos = self.complete_repo_name(
                text, line, begidx, endidx, suffix=':'
            )

        filenames = self.complete_filenames(text, line, begidx, endidx)
        return repos + filenames

    def do_setup_for_pypi_python_org(self, repo):
        '''
        Configure repo to point to the default package index
        https://pypi.python.org.
        '''
        self.repo_manager.set(
            repo,
            repomanager.KEY_TYPE,
            repomanager.REPOTYPE_HTTP
        )
        self.repo_manager.set(
            repo,
            repomanager.KEY_DOWNLOAD_URL,
            'https://pypi.python.org/simple/'
        )
        self.repo_manager.set(
            repo,
            repomanager.KEY_UPLOAD_URL,
            'https://pypi.python.org/'
        )

    complete_setup_for_pypi_python_org = complete_repo_name

    def do_setup_for_pip_local(self, repo):
        '''
        Configure repo to be directory based with directory `~/.pip/local`.
        Also makes that directory if needed.
        '''
        piplocal = os.path.expanduser('~/.pip/local')
        if not os.path.exists(piplocal):
            os.makedirs(piplocal)
        self.repo_manager.set(
            repo,
            repomanager.KEY_TYPE,
            repomanager.REPOTYPE_DIRECTORY
        )
        self.repo_manager.set(
            repo,
            repomanager.KEY_DIRECTORY,
            piplocal
        )

    complete_setup_for_pip_local = complete_repo_name
