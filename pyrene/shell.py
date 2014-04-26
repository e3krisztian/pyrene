# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import os
from cmd import Cmd
import traceback
from .util import write_file, bold
from .network import Network, DirectoryRepo
from .constants import REPO, REPOTYPE


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

    def completenames(self, *args):
        # when there is only one completions, add an extra space
        completions = super(BaseCmd, self).completenames(*args)
        if len(completions) == 1:
            return [completions[0].rstrip() + ' ']
        return completions


REPO_ATTRIBUTE_COMPLETIONS = tuple(
    '{}='.format(a)
    for a in Network.REPO_ATTRIBUTES
)


class PyreneCmd(BaseCmd):

    intro = '''
    Pyrene provides tools to work with different repos of python packages.

    e.g. one might use three different repos in one project:

     - pypi.python.org       (globally shared)
     - private pypi instance (project/company specific,
                              pip needs to be configured to fetch from here)
     - developer cache       (~/.pip/local)

    For help on commands type {help} or {qmark}
    '''.format(help=bold('help'), qmark=bold('?'))
    prompt = 'Pyrene: '

    def __init__(self, network, directory):
        super(PyreneCmd, self).__init__()
        self.network = network
        self.__temp_dir = directory

    def precmd(self, line):
        self.network.reload()
        return super(PyreneCmd, self).precmd(line)

    def write_file(self, filename, content):
        write_file(filename, content)

    def do_write_pip_conf_for(self, repo):
        '''
        Set up pip to use REPO by default (write ~/.pip/pip.conf)

        write_pip_conf_for REPO
        '''
        repo = self.network.get_repo(repo)
        pip_conf = os.path.expanduser('~/.pip/pip.conf')
        self.write_file(pip_conf, repo.get_as_pip_conf().encode('utf8'))

    def _get_destination_repo(self, word):
        if word.endswith(':'):
            repo_name = word[:-1]
            return self.network.get_repo(repo_name)

        attributes = {'directory': word}
        return DirectoryRepo('Implicit({})'.format(word), attributes)

    def do_copy(self, line):
        '''
        Copy packages between repos

        copy [LOCAL-FILE [...]] [REPO:PACKAGE-SPEC [...]] DESTINATION

        The order of attributes is important:
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
                repo = self.network.get_repo(repo_name)
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
        self.network.define(repo)

    def do_forget(self, repo):
        '''
        Drop definition of a repo.

        forget REPO
        '''
        self.network.forget(repo)

    def do_set(self, line):
        '''
        Set repository attributes.

        set repo attribute=value

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
        repo, attribute_value = line.split()
        attribute, _, value = attribute_value.partition('=')
        self.network.set(repo, attribute, value)

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
                completions = tuple(Network.REPO_TYPES)
        else:
            completions = REPO_ATTRIBUTE_COMPLETIONS
        return sorted(c for c in completions if c.startswith(text))

    def do_unset(self, line):
        '''
        Unset a repository attribute
        '''
        repo, attribute = line.split()
        self.network.unset(repo, attribute)

    def complete_unset(self, text, line, begidx, endidx):
        complete_line = line[:endidx]
        words = complete_line.split()
        complete_index = len(words) + (0 if text else 1)
        if complete_index == 2:
            completions = self.complete_repo_name(
                text, line, begidx, endidx, suffix=' '
            )
        else:
            repo = self.network.get_repo(words[1])
            completions = repo.attributes.keys()
        return sorted(c for c in completions if c.startswith(text))

    def do_list(self, line):
        '''
        List known repos
        '''
        repo_names = self.network.repo_names
        print('Known repos:')
        print('    ' + '\n    '.join(repo_names))

    def do_show(self, repo):
        '''
        List repo attributes - as could be specified in pip.conf
        '''
        repo = self.network.get_repo(repo)
        repo.print_attributes()

    def complete_repo_name(self, text, line, begidx, endidx, suffix=''):
        return sorted(
            '{}{}'.format(name, suffix)
            for name in self.network.repo_names
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
        self.network.set(repo, REPO.TYPE, REPOTYPE.HTTP)
        self.network.set(
            repo,
            REPO.DOWNLOAD_URL,
            'https://pypi.python.org/simple/'
        )
        self.network.set(
            repo,
            REPO.UPLOAD_URL,
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
        self.network.set(repo, REPO.TYPE, REPOTYPE.DIRECTORY)
        self.network.set(repo, REPO.DIRECTORY, piplocal)

    complete_setup_for_pip_local = complete_repo_name

    def do_serve(self, repo_name):
        '''
        Serve a local directory over http as a package index (like pypi).
        Intended for quick package exchanges.
        '''
        repo = self.network.get_repo(repo_name)
        repo.serve()

    complete_serve = complete_repo_name
