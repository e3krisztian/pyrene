# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import os
from cmd import Cmd
import traceback
from .util import write_file, bold, red
from .network import Network, DirectoryRepo, UnknownRepoError
from .constants import REPO, REPOTYPE


class ShellError(Exception):

    def __init__(self, message):
        self.message = message


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

    def onecmd(self, line):
        try:
            return super(BaseCmd, self).onecmd(line)
        except ShellError as e:
            print(red('ERROR: {}'.format(e.message)))

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

    @property
    def prompt(self):
        active_repo = self.network.active_repo
        prompt = (
            'Pyrene[{}]: '.format(active_repo) if active_repo
            else 'Pyrene: '
        )
        return prompt

    def __init__(self, network, directory):
        super(PyreneCmd, self).__init__()
        self.network = network
        self.__temp_dir = directory

    def precmd(self, line):
        self.network.reload()
        return super(PyreneCmd, self).precmd(line)

    def write_file(self, filename, content):
        write_file(filename, content)

    def abort_on_unknown_repository_name(self, repo_name, command):
        if repo_name not in self.network.repo_names:
            raise ShellError('Unknown repository: {}'.format(repo_name))

    def get_effective_repo_name(self, repo_name):
        return repo_name or self.network.active_repo

    def abort_on_missing_effective_repo_name(self, repo_name, command):
        if not self.get_effective_repo_name(repo_name):
            raise ShellError(
                (
                    'Command "{}" requires a repository,'
                    + ' but none was given or active'
                ).format(command)
            )

    def abort_on_nonexisting_effective_repo(self, repo_name, command):
        self.abort_on_missing_effective_repo_name(repo_name, command)
        self.abort_on_unknown_repository_name(
            self.get_effective_repo_name(repo_name),
            command
        )

    def abort_on_nonexisting_repo(self, repo_name, command):
        if not repo_name:
            raise ShellError(
                'Command "{}" requires a repository parameter'
                .format(command)
            )

        self.abort_on_unknown_repository_name(repo_name, command)

    def do_use(self, repo):
        self.abort_on_nonexisting_effective_repo(repo, 'use')

        repo = self.network.get_repo(repo)
        pip_conf = os.path.expanduser('~/.pip/pip.conf')
        self.write_file(pip_conf, repo.get_as_pip_conf().encode('utf8'))

    def help_use(self):
        help = '''
        Set up {pip} (when used outside of Pyrene) to use REPO by default.

        {warn}
        '''.format(
            pip=bold('pip'),
            warn=red('WARNING: Overwrites ~/.pip/pip.conf!')
        )
        print(help)

    def _get_destination_repo(self, word):
        if word.endswith(':'):
            repo_name = word[:-1]
            try:
                return self.network.get_repo(repo_name)
            except UnknownRepoError:
                raise ShellError(
                    'Repository {} is not known'.format(repo_name)
                )

        attributes = {'directory': word}
        return DirectoryRepo('Implicit({})'.format(word), attributes)

    def do_copy(self, line):
        '''
        Copy packages between repos

          copy SOURCE DESTINATION

        Where SOURCE can be either LOCAL-FILE or REPO:PACKAGE-SPEC
        DESTINATION can be either a REPO: or a directory.
        '''
        words = line.split()
        source, destination = words
        destination_repo = self._get_destination_repo(destination)
        local_file_source = ':' not in source

        if local_file_source:
            destination_repo.upload_packages([source])
        else:
            source_repo_name, _, package_spec = source.partition(':')
            try:
                source_repo = self.network.get_repo(source_repo_name)
            except UnknownRepoError:
                raise ShellError(
                    'Unknown repository {}'.format(source_repo_name)
                )

            # copy between repos with the help of temporary storage
            try:
                source_repo.download_packages(package_spec, self.__temp_dir)
                destination_repo.upload_packages(self.__temp_dir.files)
            finally:
                self.__temp_dir.clear()

    def do_work_on(self, repo):
        '''
        Make repo the active one.
        Commands working on a repo will use it as default for repo parameter.
        '''
        self.abort_on_nonexisting_repo(repo, 'work_on')
        self.network.active_repo = repo

    def __define_or_change_type(self, repo, repotype):
        effective_repo_name = self.get_effective_repo_name(repo)
        if effective_repo_name not in self.network.repo_names:
            self.network.define(effective_repo_name)
        self.network.active_repo = effective_repo_name
        self.network.set(effective_repo_name, REPO.TYPE, repotype)

    def do_http_repo(self, repo):
        '''
        [Re]define REPO as http package repository.

        http_repo REPO
        '''
        self.abort_on_missing_effective_repo_name(repo, 'http_repo')
        self.__define_or_change_type(repo, REPOTYPE.HTTP)

    def do_directory_repo(self, repo):
        '''
        [Re]define REPO as directory package repository.

        directory_repo REPO
        '''
        self.abort_on_missing_effective_repo_name(repo, 'directory_repo')
        self.__define_or_change_type(repo, REPOTYPE.DIRECTORY)

    def do_forget(self, repo):
        '''
        Drop definition of a repo.

        forget REPO
        '''
        self.abort_on_nonexisting_repo(repo, 'forget')
        self.network.forget(repo)

    def abort_on_invalid_active_repo(self, command):
        if self.network.active_repo not in self.network.repo_names:
            raise ShellError(
                'Command "{}" requires a valid repository to be worked on'
                .format(command)
            )

    def do_set(self, line):
        '''
        Set repository attributes on the active repo.

        set attribute=value

        # intended use:

        # directory repos:
        work_on developer-repo
        set type=directory
        set directory=package-directory

        # http repos:
        work_on company-private-repo
        set type=http
        set download-url=http://...
        set upload-url=http://...
        set username=user
        set password=pass
        '''
        self.abort_on_invalid_active_repo('set')
        repo = self.network.active_repo
        attribute, eq, value = line.partition('=')
        if not attribute:
            raise ShellError('command "set" requires a non-empty attribute')
        if not eq:
            raise ShellError('command "set" requires a value')
        self.network.set(repo, attribute, value)

    def complete_set(self, text, line, begidx, endidx):
        completions = set()
        complete_line = line[:endidx]
        words = complete_line.split()
        if '=' in words[-1]:
            attribute, _, value = words[-1].partition('=')
            if attribute == 'type':
                completions = set(Network.REPO_TYPES)
            if self.network.active_repo:
                attributes = self.network.get_attributes(
                    self.network.active_repo
                )
                if attribute in attributes:
                    completions.add(attributes[attribute])
        else:
            completions = REPO_ATTRIBUTE_COMPLETIONS
        return sorted(c for c in completions if c.startswith(text))

    def do_unset(self, attribute):
        '''
        Unset attribute on the active/default repo
        '''
        self.abort_on_invalid_active_repo('unset')
        if not attribute:
            raise ShellError('command "unset" requires a non-empty attribute')
        self.network.unset(self.network.active_repo, attribute)

    def complete_unset(self, text, line, begidx, endidx):
        repo_name = self.network.active_repo
        if not repo_name:
            return []
        repo = self.network.get_repo(repo_name)
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
        List repo attributes
        '''
        self.abort_on_nonexisting_effective_repo(repo, 'show')

        repo = self.network.get_repo(repo)
        repo.print_attributes()

    def do_setup_for_pypi_python_org(self, repo):
        '''
        Configure repo to point to the default package index
        https://pypi.python.org.
        '''
        effective_repo_name = self.get_effective_repo_name(repo)
        self.abort_on_nonexisting_repo(
            effective_repo_name, 'setup_for_pypi_python_org'
        )

        self.network.set(effective_repo_name, REPO.TYPE, REPOTYPE.HTTP)
        self.network.set(
            effective_repo_name,
            REPO.DOWNLOAD_URL,
            'https://pypi.python.org/simple/'
        )
        self.network.set(
            effective_repo_name,
            REPO.UPLOAD_URL,
            'https://pypi.python.org/pypi'
        )

    def do_setup_for_pip_local(self, repo):
        '''
        Configure repo to be directory based with directory `~/.pip/local`.
        Also makes that directory if needed.
        '''
        effective_repo_name = self.get_effective_repo_name(repo)
        self.abort_on_nonexisting_repo(
            effective_repo_name, 'setup_for_pip_local'
        )

        piplocal = os.path.expanduser('~/.pip/local')
        if not os.path.exists(piplocal):
            os.makedirs(piplocal)
        self.network.set(effective_repo_name, REPO.TYPE, REPOTYPE.DIRECTORY)
        self.network.set(effective_repo_name, REPO.DIRECTORY, piplocal)

    def do_serve(self, repo_name):
        '''
        Serve a local directory over http as a package index (like pypi).
        Intended for quick package exchanges.
        '''
        self.abort_on_nonexisting_effective_repo(repo_name, 'serve')

        repo = self.network.get_repo(repo_name)
        repo.serve()

    def complete_repo_name(self, text, line, begidx, endidx, suffix=''):
        return sorted(
            '{}{}'.format(name, suffix)
            for name in self.network.repo_names
            if name.startswith(text)
        )

    complete_http_repo = complete_repo_name
    complete_directory_repo = complete_repo_name
    complete_work_on = complete_repo_name
    complete_forget = complete_repo_name
    complete_show = complete_repo_name
    complete_use = complete_repo_name
    complete_setup_for_pypi_python_org = complete_repo_name
    complete_setup_for_pip_local = complete_repo_name
    complete_serve = complete_repo_name

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
