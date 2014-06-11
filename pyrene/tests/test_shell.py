# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import os

import fixtures
import unittest
import mock
from temp_dir import within_temp_dir
import tempfile

import pyrene.shell as m
from pyrene.util import Directory
from pyrene.repos import Repo
from pyrene.constants import REPOTYPE
from .util import capture_stdout, fake_stdin, Assertions, record_calls

write_file = m.write_file

PYPIRC_W_repo1_repo2 = b'''\
[distutils]
[repo1]
repository: repo...
username: xy
[repo2]
repository: repo...
'''


class MockingNetwork(m.Network):
    '''get_repo returns BadRepo to prevent all destructive operations'''
    TYPE_TO_CLASS = {}

    def __init__(self, dot_pyrene, get_repo):
        super(MockingNetwork, self).__init__(dot_pyrene)
        self.__get_repo = get_repo

    def get_repo(self, repo_name):
        repo = self.__get_repo(repo_name)
        return (
            repo if repo
            else super(MockingNetwork, self).get_repo(repo_name)
        )


class Test_PyreneCmd_write_file(unittest.TestCase):

    def setUp(self):
        super(Test_PyreneCmd_write_file, self).setUp()
        self.network = mock.Mock(spec_set=m.Network)
        self.directory = mock.Mock(spec_set=Directory)
        self.pypirc = mock.Mock(os.devnull)
        self.cmd = m.PyreneCmd(
            network=self.network,
            directory=self.directory,
            pypirc=self.pypirc,
        )

    @within_temp_dir
    def test_creates_subdirectories(self):
        self.cmd.write_file('subdir/test-file', b'somecontent')
        with open('subdir/test-file', 'rb') as f:
            self.assertEqual(b'somecontent', f.read())

    @within_temp_dir
    def test_does_not_resolve_tilde(self):
        self.cmd.write_file('~', b'somecontent')
        with open('~', 'rb') as f:
            self.assertEqual(b'somecontent', f.read())


class Test_PyreneCmd(Assertions, fixtures.TestWithFixtures):

    def setUp(self):
        super(Test_PyreneCmd, self).setUp()
        self.repo1 = mock.Mock(spec_set=Repo)
        self.repo2 = mock.Mock(spec_set=Repo)
        self.somerepo = mock.Mock(spec_set=Repo)

        self.home_dir = fixtures.TempHomeDir()
        self.useFixture(self.home_dir)
        self.dot_pyrene = os.path.expanduser('~/.pyrene')
        self.dot_pypirc = os.path.expanduser('~/.pypirc')
        self.dot_pipconf = os.path.expanduser('~/.pip/pip.conf')
        assert self.dot_pyrene.startswith(self.home_dir.path)
        assert self.dot_pypirc.startswith(self.home_dir.path)
        self.network = MockingNetwork(self.dot_pyrene, self.get_repo)

        self.directory = mock.Mock(spec_set=Directory)
        self.directory.files = ()
        self.cmd = m.PyreneCmd(
            network=self.network,
            directory=self.directory,
            pypirc=self.dot_pypirc,
        )
        # count writes?
        self.cmd.write_file = mock.Mock(side_effect=self.cmd.write_file)

    def define_repos(self, *repo_names):
        for repo_name in repo_names:
            self.network.define(repo_name)

    def define_repo(self, repo_name, attributes):
        self.network.define(repo_name)
        self.network.active_repo = repo_name
        for attr, value in attributes.items():
            self.network.set(repo_name, attr, value)

    def get_repo(self, repo_name):
        if repo_name == 'repo1':
            return self.repo1
        if repo_name == 'repo2':
            return self.repo2
        if repo_name == 'somerepo':
            return self.somerepo

    def test_use(self):
        self.network.define('somerepo')
        self.network.get_repo = mock.Mock(return_value=self.somerepo)
        pip_conf = 'someconf'
        self.somerepo.get_as_pip_conf.configure_mock(
            return_value=pip_conf
        )

        self.cmd.onecmd('use somerepo')

        self.cmd.write_file.assert_called_once_with(
            os.path.expanduser('~/.pip/pip.conf'),
            pip_conf.encode('utf8')
        )

    def test_use_with_unknown_repo(self):
        output = run_script(self.cmd, 'use undefined')

        self.assertContainsInOrder(
            output,
            ('ERROR:', 'Unknown repo', 'undefined')
        )
        self.assertEqual(0, self.cmd.write_file.call_count)

    def test_use_with_implicit_repo(self):
        output = run_script(
            self.cmd,
            '''
            directory_repo somerepo
            work_on somerepo
            use
            '''
        )

        self.assertNotIn('ERROR:', output)
        self.assertEqual(1, self.cmd.write_file.call_count)

    def test_use_creates_backup_of_pip_conf(self):
        SOMECONTENT = b'sometext'
        SOMECONTENT_MD5 = 'a29e90948f4eee52168fab5fa9cfbcf8'
        write_file(self.dot_pipconf, SOMECONTENT)
        run_script(
            self.cmd,
            '''
            directory_repo somerepo
            setup_for_pip_local somerepo
            use
            ''',
        )
        backup = '{}.{}'.format(self.dot_pipconf, SOMECONTENT_MD5)
        with open(backup, 'rb') as f:
            self.assertEqual(SOMECONTENT, f.read())

    def test_use_with_missing_implicit_repo(self):
        output = run_script(self.cmd, 'use')

        self.assertIn('ERROR:', output)
        self.assertEqual(0, self.cmd.write_file.call_count)

    def test_copy_single_package(self):
        self.define_repos('repo1', 'repo2')
        self.directory.files = ['roman-2.0.0.zip']

        self.cmd.onecmd('copy repo1:roman==2.0.0 repo2:')

        self.repo1.download_packages.assert_called_once_with(
            'roman==2.0.0',
            self.directory
        )
        self.repo2.upload_packages.assert_called_once_with(['roman-2.0.0.zip'])

    def test_copy_uses_repo_to_download_packages(self):
        self.define_repos('repo1', 'repo2')

        self.cmd.onecmd('copy repo1:roman==2.0.0 repo2:')

        self.repo1.download_packages.assert_called_once_with(
            'roman==2.0.0',
            self.directory
        )

    def test_copy_uses_repo_to_upload_packages(self):
        self.define_repos('repo1', 'repo2')
        self.directory.files = ['roman-2.0.0.zip']

        self.cmd.onecmd('copy repo1:roman==2.0.0 repo2:')

        self.repo2.upload_packages.assert_called_once_with(['roman-2.0.0.zip'])

    def test_copy_package_with_dependencies(self):
        self.define_repos('repo1', 'repo2')
        package_files = ('pkg-1.0.0.tar.gz', 'dep-0.3.1.zip')
        self.directory.files = list(package_files)

        self.cmd.onecmd('copy repo1:pkg repo2:')

        self.repo1.download_packages.assert_called_once_with(
            'pkg',
            self.directory
        )
        self.repo2.upload_packages.assert_called_once_with(list(package_files))

    def test_copy_uploads_files(self):
        self.define_repos('somerepo')
        self.cmd.onecmd('copy /a/file somerepo:')

        self.somerepo.upload_packages.assert_called_once_with(
            ['/a/file']
        )

    def test_copy_from_unknown_repo(self):
        output = run_script(
            self.cmd,
            '''
            directory_repo somerepo
            copy unknown:pkg somerepo:
            '''
        )

        self.assertContainsInOrder(output, ('ERROR:', 'unknown'))
        self.assertEqual(0, self.somerepo.upload_packages.call_count)

    def test_copy_to_unknown_repo(self):
        self.directory.files = ['/tmp/downloaded-package-file']
        output = run_script(
            self.cmd,
            '''
            directory_repo somerepo
            copy somerepo:pkg unknown:
            '''
        )

        self.assertContainsInOrder(output, ('ERROR:', 'unknown'))
        self.assertEqual(0, self.somerepo.upload_packages.call_count)

    def test_get_destination_repo_on_repo1(self):
        self.define_repos('repo1')
        repo = self.cmd._get_destination_repo('repo1:')
        self.assertIs(self.repo1, repo)

    def test_get_destination_repo_on_directory(self):
        repo = self.cmd._get_destination_repo('/path/to/directory')
        self.assertEqual('/path/to/directory', repo.directory)

    def test_copy_with_directory_destination(self):
        self.define_repos('repo1')
        self.directory.files = ['a-pkg']
        self.cmd._get_destination_repo = mock.Mock(
            return_value=self.somerepo
        )

        self.cmd.onecmd('copy repo1:a /tmp/x')
        self.cmd._get_destination_repo.assert_called_once_with('/tmp/x')
        self.somerepo.upload_packages.assert_called_once_with(['a-pkg'])

    def test_copy_clears_directory_after_upload(self):
        self.define_repos('repo1', 'repo2')
        package_files = ('pkg-1.0.0.tar.gz', 'dep-0.3.1.zip')
        files = mock.PropertyMock(return_value=list(package_files))
        type(self.directory).files = files

        self.cmd.onecmd('copy repo1:pkg repo2:')

        files.assert_called_once_with()
        self.assertEqual(
            [mock.call.clear()],
            self.directory.mock_calls
        )

    def test_copy_clears_directory_even_if_download_fails(self):
        self.define_repos('repo1', 'repo2')
        self.repo1.download_packages.configure_mock(side_effect=Exception)

        try:
            self.cmd.onecmd('copy repo1:a repo2:')
        except:
            pass

        self.assertIn(mock.call.clear(), self.directory.mock_calls)

    def test_http_repo_defines_new_repo(self):
        output = run_script(
            self.cmd,
            '''
            http_repo new-repo
            list
            '''
        )

        self.assertIn('new-repo', output)

    def test_existing_repo_http_repo_changes_repo_type(self):
        run_script(
            self.cmd,
            '''
            directory_repo new-repo
            set attr=somevalue
            http_repo
            '''
        )

        self.assertEqual('new-repo', self.network.active_repo)
        repo = self.network.get_repo('new-repo')
        self.assertEqual(REPOTYPE.HTTP, repo.type)
        self.assertEqual('somevalue', repo.attr)

    def test_directory_repo_defines_new_repo(self):
        output = run_script(
            self.cmd,
            '''
            directory_repo new-repo
            list
            '''
        )

        self.assertIn('new-repo', output)

    def test_existing_repo_directory_repo_changes_repo_type(self):
        run_script(
            self.cmd,
            '''
            http_repo new-repo
            set attr=somevalue
            directory_repo
            '''
        )

        self.assertEqual('new-repo', self.network.active_repo)
        repo = self.network.get_repo('new-repo')
        self.assertEqual(REPOTYPE.DIRECTORY, repo.type)
        self.assertEqual('somevalue', repo.attr)

    def test_forget(self):
        self.network.define('somerepo')

        self.cmd.onecmd('forget somerepo')

        self.assertNotIn('somerepo', self.network.repo_names)

    def test_unset(self):
        output = run_script(
            self.cmd,
            '''
            http_repo repo
            set someattribute=value
            unset someattribute
            set someotherattribute=othervalue
            show repo
            '''
        )

        self.assertNotIn('someattribute', output)
        self.assertIn('someotherattribute', output)

    def test_list(self):
        self.define_repos('S1', '#@!')

        with capture_stdout() as stdout:
            self.cmd.onecmd('list')
            output = stdout.content

        self.assertIn('S1', output)
        self.assertIn('#@!', output)

    def test_show(self):
        output = run_script(
            self.cmd,
            '''
            directory_repo repo
            set name=SHRP1
            set type=??
            show repo
            '''
        )

        self.assertIn('SHRP1', output)
        self.assertIn('??', output)

    def test_status(self):
        with capture_stdout() as stdout:
            self.cmd.onecmd('status')
            output = stdout.content

        self.assertIn('Pyrene', output)
        self.assertIn('version', output)
        self.assertIn('pypirc', output)
        self.assertIn('pip.conf', output)

    def test_complete_set_on_attribute(self):
        completion = self.cmd.complete_set('', 'set atibute=value', 4, 4)
        self.assertEqual(set(m.REPO_ATTRIBUTE_COMPLETIONS), set(completion))

    def test_complete_set_on_attribute_ty(self):
        completion = self.cmd.complete_set('ty', 'set ty=value', 4, 6)
        self.assertEqual({'type='}, set(completion))

    def test_complete_set_on_type_value_fi(self):
        completion = self.cmd.complete_set('di', 'set type=di', 9, 11)
        self.assertEqual(['directory'], completion)

    def test_complete_set_on_empty_type_value(self):
        completion = self.cmd.complete_set('', 'set type=', 9, 9)
        self.assertEqual(set(m.Network.REPO_TYPES), set(completion))

    def test_complete_set_completes_existing_attribute_value(self):
        run_script(
            self.cmd,
            '''
            directory_repo repo
            set attr=somevalue
            '''
        )
        completion = self.cmd.complete_set('', 'set attr=', 9, 9)
        self.assertEqual({'somevalue'}, set(completion))

    def test_complete_set_on_value(self):
        completion = self.cmd.complete_set(
            'attribute=', 'set re attribute=value', 7, 17
        )
        self.assertEqual(set(), set(completion))

    def test_complete_unset_on_attribute_name(self):
        self.define_repo('repo', {'a': '1', 'b': '2'})
        completion = self.cmd.complete_unset('', 'unset ', 6, 6)
        self.assertEqual({'a', 'b'}, set(completion))

    def test_complete_repo_name(self):
        self.define_repos('repo', 'repo2')
        completion = self.cmd.complete_repo_name('', 'cmd ', 4, 4)
        self.assertEqual({'repo', 'repo2'}, set(completion))

    def test_complete_repo_name_with_suffix(self):
        self.define_repos('repo', 'repo2')
        completion = self.cmd.complete_repo_name('', 'cmd ', 4, 4, suffix=':')
        self.assertEqual({'repo:', 'repo2:'}, set(completion))

    def test_complete_repo_name_returns_sorted_output(self):
        self.define_repos('c-repo', 'repo-b', 'repo-a')
        completion = self.cmd.complete_repo_name('re', 'cmd re', 4, 6)
        self.assertEqual(['repo-a', 'repo-b'], completion)

    def test_complete_copy_completes_repos(self):
        self.define_repos('repo', 'repo2')
        completion = self.cmd.complete_copy('', 'copy ', 5, 5)
        self.assertTrue({'repo:', 'repo2:'}.issubset(set(completion)))

    @within_temp_dir
    def test_complete_filenames(self):
        os.makedirs('a')
        os.makedirs('c')
        write_file('ef', b'')

        completion = self.cmd.complete_filenames('', 'cmd ', 4, 4)

        self.assertEqual(['a/', 'c/', 'ef'], completion)

    @within_temp_dir
    def test_complete_filenames_with_prefix(self):
        os.makedirs('aa')

        completion = self.cmd.complete_filenames('a', 'cmd a', 4, 5)

        self.assertEqual(['aa/'], completion)

    @within_temp_dir
    def test_complete_filenames_with_nonexistent_prefix(self):
        completion = self.cmd.complete_filenames('a', 'cmd a/b/', 4, 8)

        self.assertEqual([], completion)

    @within_temp_dir
    def test_complete_filenames_with_subpaths(self):
        write_file('a/b/c', b'')

        completion = self.cmd.complete_filenames('', 'cmd a/b/', 6, 6)

        self.assertEqual(['b/'], completion)

    @within_temp_dir
    def test_complete_copy_completes_directories(self):
        os.makedirs('dir3/dir2/dir1')

        completion = self.cmd.complete_copy('', 'copy ', 4, 4)

        self.assertTrue({'dir3/'}.issubset(set(completion)))

    @within_temp_dir
    def test_complete_copy_does_not_complete_repos_after_slash(self):
        os.makedirs('dir')
        self.define_repos('repo', 'repo2')

        completion = self.cmd.complete_copy('', 'copy ./', 7, 7)

        self.assertEqual(['dir/'], completion)

    @within_temp_dir
    def test_complete_copy_does_not_complete_filenames_after_a_repo(self):
        os.makedirs('dir')
        self.define_repos('repo', 'repo2')

        completion = self.cmd.complete_copy('', 'copy repo:', 10, 10)

        self.assertEqual([], completion)

    def test_setup_for_pypi_python_org(self):
        self.define_repos('repo')

        self.cmd.onecmd('setup_for_pypi_python_org repo')

        repo = self.network.get_repo('repo')
        self.assertIn('pypi.python.org', repo.download_url)

    def test_setup_for_pip_local(self):
        self.define_repos('repo')

        self.cmd.onecmd('setup_for_pip_local repo')

        repo = self.network.get_repo('repo')
        self.assertIn('pip/local', repo.directory)

    def test_serve(self):
        self.define_repos('repo1')

        self.cmd.onecmd('serve repo1')

        self.repo1.serve.assert_called_once_with()

    def test_network_reload_called_before_every_command_in_the_loop(self):
        calls = []
        self.network.reload = record_calls(calls, self.network.reload)
        self.define_repos('repo-a')

        run_script(self.cmd, '\nlist\n')

        # expect 3 calls, one for each of
        # empty line
        # list
        # EOF
        self.assertEqual(3, len(calls))

    def test_define_sets_default_repo(self):
        script = '''
        http_repo repo
        set someattr=somevalue
        show repo
        '''
        output = run_script(self.cmd, script)
        self.assertContainsInOrder(output, ['someattr', 'somevalue'])

    def test_work_on_sets_prompt(self):
        output = run_script(
            self.cmd,
            '''
            http_repo somerepo
            work_on somerepo
            '''
        )
        self.assertIn('Pyrene[somerepo]: ', output)

    def test_import_pypirc(self):
        write_file(self.dot_pypirc, PYPIRC_W_repo1_repo2)
        output = run_script(
            self.cmd,
            '''
            import_pypirc
            list
            '''
        )
        self.assertIn('repo1', output)
        self.assertIn('repo2', output)


def run_script(cmd, script):
    with fake_stdin(script):
        with capture_stdout() as stdout:
            cmd.cmdloop()
            return stdout.content


#########################################################
import nose.util


# nose specific: uses test generators for checking all commands
class Test_PyreneCmd_repo_parameter_checking(Assertions):

    def setup(self):
        self.home_dir = fixtures.TempHomeDir()
        self.home_dir.setUp()
        self.dot_pyrene = tempfile.NamedTemporaryFile()
        self.network = m.Network(self.dot_pyrene.name)

        self.directory = mock.Mock(spec_set=Directory)
        self.directory.files = ('dummy')
        self.cmd = m.PyreneCmd(
            network=self.network,
            directory=self.directory,
            pypirc=os.devnull,
        )
        self.cmd.write_file = mock.Mock()

    def teardown(self):
        try:
            self.dot_pyrene.close()
        finally:
            self.home_dir.cleanUp()

    def test_requires_explicit_repo_parameter(self):
        commands = [
            'forget',
            'work_on',
        ]
        for command in commands:
            yield self.check_requires_repo_parameter, command

    def check_requires_repo_parameter(self, command):
        output = run_script(
            self.cmd,
            '''
            directory_repo somerepo
            work_on somerepo
            {}
            '''.format(command)
        )
        self.assertContainsInOrder(output, ('ERROR', command, 'requires'))

    def test_active_repo_works(self):
        commands = [
            'use',
            # 'forget',
            'show',
            'setup_for_pip_local',
            'setup_for_pypi_python_org',
            'serve',
            # 'work_on',
            'directory_repo',
            'http_repo',
        ]
        for command in commands:
            yield self.check_active_repo_works_for, command

    def check_active_repo_works_for(self, command):
        output = run_script(
            self.cmd,
            '''
            http_repo somerepo
            set download_url=http://example.com:8080/simple
            work_on somerepo
            {}
            '''.format(command)
        )
        nose.tools.assert_not_in('ERROR', output)

    def test_missing_active_repo_error_message(self):
        commands = [
            'use',
            'forget',
            'show',
            'setup_for_pip_local',
            'setup_for_pypi_python_org',
            'serve',
            'work_on',
            'directory_repo',
            'http_repo',
        ]
        for command in commands:
            yield self.check_missing_active_repo_error_message, command

    def check_missing_active_repo_error_message(self, command):
        output = run_script(
            self.cmd,
            '''
            {}
            '''.format(command)
        )
        self.assertContainsInOrder(output, ('ERROR', command, 'requires'))

    def test_active_repo_only_error_message(self):
        commands = [
            ('set', 'attr=value'),
            ('unset', 'attr'),
        ]
        for command, param in commands:
            yield self.check_active_repo_only_error_message, command, param

    def check_active_repo_only_error_message(self, command, param):
        output = run_script(
            self.cmd,
            '''
            {} {}
            '''.format(command, param)
        )
        self.assertContainsInOrder(
            output,
            ('ERROR', command, 'requires', 'work')
        )

    def test_unknown_repo_error_message(self):
        commands = [
            'use',
            'forget',
            'show',
            'setup_for_pip_local',
            'setup_for_pypi_python_org',
            'serve',
            'work_on',
            # 'directory_repo',
            # 'http_repo',
        ]
        for command in commands:
            yield self.check_unknown_repo_error_message, command

    def check_unknown_repo_error_message(self, command):
        output = run_script(
            self.cmd,
            '''
            {} undefined-repo
            '''.format(command)
        )
        self.assertContainsInOrder(output, ('ERROR', 'undefined-repo'))

    def test_set_without_parameter(self):
        output = run_script(
            self.cmd,
            '''
            directory_repo repo
            set
            '''
        )
        self.assertContainsInOrder(
            output,
            ('ERROR', 'set', 'requires', 'attribute')
        )

    def test_set_without_equal_sign(self):
        output = run_script(
            self.cmd,
            '''
            directory_repo repo
            set attr
            '''
        )
        self.assertContainsInOrder(
            output,
            ('ERROR', 'set', 'requires', 'value')
        )

    def test_unset_without_attribute(self):
        output = run_script(
            self.cmd,
            '''
            directory_repo repo
            unset
            '''
        )
        self.assertContainsInOrder(
            output,
            ('ERROR', 'unset', 'requires', 'attribute')
        )

# TODO: tests for error cases in copy
