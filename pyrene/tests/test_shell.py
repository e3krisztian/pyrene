# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import os

import unittest
import mock
from temp_dir import within_temp_dir

import pyrene.shell as m
from pyrene.util import Directory
from pyrene.constants import REPO
from pyrene.repos import Repo
from .util import capture_stdout, fake_stdin

write_file = m.write_file


class Test_PyreneCmd_write_file(unittest.TestCase):

    def setUp(self):
        self.network = mock.Mock(spec_set=m.Network)
        self.directory = mock.Mock(spec_set=Directory)
        self.cmd = m.PyreneCmd(
            network=self.network,
            directory=self.directory
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


class Test_PyreneCmd(unittest.TestCase):

    def setUp(self):
        self.repo1 = mock.Mock(spec_set=Repo)
        self.repo2 = mock.Mock(spec_set=Repo)
        self.somerepo = mock.Mock(spec_set=Repo)
        self.network = mock.Mock(spec_set=m.Network)
        self.network.get_repo.configure_mock(side_effect=self.get_repo)
        self.directory = mock.Mock(spec_set=Directory)
        self.directory.files = ()
        self.cmd = m.PyreneCmd(
            network=self.network,
            directory=self.directory
        )
        self.cmd.write_file = mock.Mock()

    def get_repo(self, repo_name):
        if repo_name == 'repo1':
            return self.repo1
        if repo_name == 'repo2':
            return self.repo2
        if repo_name == 'somerepo':
            return self.somerepo

    def test_write_pip_conf_for(self):
        pip_conf = 'someconf'
        self.somerepo.get_as_pip_conf.configure_mock(
            return_value=pip_conf
        )

        self.cmd.onecmd('write_pip_conf_for somerepo')

        self.somerepo.get_as_pip_conf.assert_called_once_with()
        self.cmd.write_file.assert_called_once_with(
            os.path.expanduser('~/.pip/pip.conf'),
            pip_conf.encode('utf8')
        )

    def test_copy_single_package(self):
        self.directory.files = ['roman-2.0.0.zip']

        self.cmd.onecmd('copy repo1:roman==2.0.0 repo2:')

        self.assertIn(mock.call.get_repo('repo1'), self.network.mock_calls)
        self.assertIn(mock.call.get_repo('repo2'), self.network.mock_calls)

        self.repo1.download_packages.assert_called_once_with(
            'roman==2.0.0',
            self.directory
        )
        self.repo2.upload_packages.assert_called_once_with(['roman-2.0.0.zip'])

    def test_copy_uses_network(self):
        self.cmd.onecmd('copy repo1:roman==2.0.0 repo2:')

        self.assertIn(mock.call.get_repo('repo1'), self.network.mock_calls)
        self.assertIn(mock.call.get_repo('repo2'), self.network.mock_calls)

    def test_copy_uses_repo_to_download_packages(self):
        self.cmd.onecmd('copy repo1:roman==2.0.0 repo2:')

        self.repo1.download_packages.assert_called_once_with(
            'roman==2.0.0',
            self.directory
        )

    def test_copy_uses_repo_to_upload_packages(self):
        self.directory.files = ['roman-2.0.0.zip']

        self.cmd.onecmd('copy repo1:roman==2.0.0 repo2:')

        self.repo2.upload_packages.assert_called_once_with(['roman-2.0.0.zip'])

    def test_copy_package_with_dependencies(self):
        package_files = ('pkg-1.0.0.tar.gz', 'dep-0.3.1.zip')
        self.directory.files = list(package_files)

        self.cmd.onecmd('copy repo1:pkg repo2:')

        self.repo1.download_packages.assert_called_once_with(
            'pkg',
            self.directory
        )
        self.repo2.upload_packages.assert_called_once_with(list(package_files))

    def test_copy_from_two_repos(self):
        package_files = ('a-1.egg', 'b-2.tar.gz')
        self.directory.files = list(package_files)

        self.cmd.onecmd('copy repo1:a repo2:b somerepo:')

        self.repo1.download_packages.assert_called_once_with(
            'a',
            self.directory
        )
        self.repo2.download_packages.assert_called_once_with(
            'b',
            self.directory
        )
        self.somerepo.upload_packages.assert_called_once_with(
            list(package_files)
        )

    def test_copy_uploads_files(self):
        self.cmd.onecmd('copy /a/file somerepo:')

        self.somerepo.upload_packages.assert_called_once_with(
            ['/a/file']
        )

    def test_copy_uploads_both_files_and_packages(self):
        self.directory.files = ['/tmp/downloaded-package-file']
        self.cmd.onecmd('copy /a/file somerepo:')

        self.somerepo.upload_packages.assert_called_once_with(
            ['/a/file', '/tmp/downloaded-package-file']
        )

    def test_get_destination_repo_on_repo1(self):
        repo = self.cmd._get_destination_repo('repo1:')
        self.assertIs(self.repo1, repo)

    def test_get_destination_repo_on_directory(self):
        repo = self.cmd._get_destination_repo('/path/to/directory')
        self.assertEqual('/path/to/directory', repo.directory)

    def test_copy_with_directory_destination(self):
        self.directory.files = ['a-pkg']
        self.cmd._get_destination_repo = mock.Mock(
            return_value=self.somerepo
        )

        self.cmd.onecmd('copy repo1:a /tmp/x')
        self.cmd._get_destination_repo.assert_called_once_with('/tmp/x')
        self.somerepo.upload_packages.assert_called_once_with(['a-pkg'])

    def test_copy_clears_directory_after_upload(self):
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
        self.repo1.download_packages.configure_mock(side_effect=Exception)

        try:
            self.cmd.onecmd('copy repo1:a repo2:')
        except:
            pass

        self.assertIn(mock.call.clear(), self.directory.mock_calls)

    def test_define(self):
        self.cmd.onecmd('define new-repo')

        self.network.define.assert_called_once_with('new-repo')

    def test_forget(self):
        self.cmd.onecmd('forget somerepo')

        self.network.forget.assert_called_once_with('somerepo')

    def test_set(self):
        self.cmd.onecmd('set repo1 attribute=value')

        self.network.set.assert_called_once_with('repo1', 'attribute', 'value')

    def test_unset(self):
        self.cmd.onecmd('unset repo1 attribute')

        self.network.unset.assert_called_once_with('repo1', 'attribute')

    def test_list(self):
        self.network.repo_names = ['S1', '#@!']

        with capture_stdout() as stdout:
            self.cmd.onecmd('list')
            output = stdout.content

        self.assertIn('S1', output)
        self.assertIn('#@!', output)

    def test_show(self):
        self.network.get_attributes.configure_mock(
            return_value={'name': 'SHRP1', REPO.TYPE: '??'}
        )

        self.cmd.onecmd('show repo1')

        self.assertEqual(
            [mock.call.get_repo('repo1')],
            self.network.mock_calls
        )
        self.repo1.print_attributes.assert_called_once_with()

    def test_complete_set_before_repo(self):
        self.network.repo_names = ('repo', 'repo2')
        completion = self.cmd.complete_set('', 'set re atibute=value', 4, 4)
        self.assertEqual({'repo ', 'repo2 '}, set(completion))

    def test_complete_set_on_repo(self):
        self.network.repo_names = ('repo', 'repo2')
        completion = self.cmd.complete_set(
            're', 'set re attribute=value', 4, 5
        )
        self.assertEqual({'repo ', 'repo2 '}, set(completion))

    def test_complete_set_on_attribute(self):
        completion = self.cmd.complete_set('', 'set re atibute=value', 7, 7)
        self.assertEqual(set(m.REPO_ATTRIBUTE_COMPLETIONS), set(completion))

    def test_complete_set_on_attribute_ty(self):
        completion = self.cmd.complete_set('ty', 'set re ty=value', 7, 9)
        self.assertEqual({'type='}, set(completion))

    def test_complete_set_on_type_value_fi(self):
        completion = self.cmd.complete_set(
            'di',
            'set re type=di',
            12,
            14,
        )
        self.assertEqual(['directory'], completion)

    def test_complete_set_on_empty_type_value(self):
        completion = self.cmd.complete_set(
            '',
            'set re type=',
            12,
            12,
        )
        self.assertEqual(set(m.Network.REPO_TYPES), set(completion))

    def test_complete_set_on_value(self):
        completion = self.cmd.complete_set(
            'attribute=', 'set re attribute=value', 7, 17
        )
        self.assertEqual(set(), set(completion))

    def test_complete_unset_without_params(self):
        self.network.repo_names = ('asd', 'absd')
        completion = self.cmd.complete_unset('', 'unset ', 6, 6)
        self.assertEqual({'asd ', 'absd '}, set(completion))

    def test_complete_unset_on_repo(self):
        self.network.repo_names = ('asd', 'absd', 'bsd')
        completion = self.cmd.complete_unset('a', 'unset as', 6, 7)
        self.assertEqual({'asd ', 'absd '}, set(completion))

    def test_complete_unset_on_attribute_name(self):
        self.repo1.attributes = {'a': 1, 'b': 2}
        completion = self.cmd.complete_unset('', 'unset repo1 ', 12, 12)
        self.assertEqual({'a', 'b'}, set(completion))

    def test_complete_repo_name(self):
        self.network.repo_names = ('repo', 'repo2')
        completion = self.cmd.complete_repo_name('', 'cmd ', 4, 4)
        self.assertEqual({'repo', 'repo2'}, set(completion))

    def test_complete_repo_name_with_suffix(self):
        self.network.repo_names = ('repo', 'repo2')
        completion = self.cmd.complete_repo_name('', 'cmd ', 4, 4, suffix=':')
        self.assertEqual({'repo:', 'repo2:'}, set(completion))

    def test_complete_repo_name_returns_sorted_output(self):
        self.network.repo_names = ('c-repo', 'repo-b', 'repo-a')
        completion = self.cmd.complete_repo_name('re', 'cmd re', 4, 6)
        self.assertEqual(['repo-a', 'repo-b'], completion)

    def test_complete_copy_completes_repos(self):
        self.network.repo_names = ('repo', 'repo2')
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
        self.network.repo_names = ('repo', 'repo2')

        completion = self.cmd.complete_copy('', 'copy ', 4, 4)

        self.assertTrue({'dir3/'}.issubset(set(completion)))

    @within_temp_dir
    def test_complete_copy_does_not_complete_repos_after_slash(self):
        os.makedirs('dir')
        self.network.repo_names = ('repo', 'repo2')

        completion = self.cmd.complete_copy('', 'copy ./', 7, 7)

        self.assertEqual(['dir/'], completion)

    @within_temp_dir
    def test_complete_copy_does_not_complete_filenames_after_a_repo(self):
        os.makedirs('dir')
        self.network.repo_names = ('repo', 'repo2')

        completion = self.cmd.complete_copy('', 'copy repo:', 10, 10)

        self.assertEqual([], completion)

    def test_setup_for_pypi_python_org(self):
        self.cmd.onecmd('setup_for_pypi_python_org repo')
        calls = [mock.call.set('repo', mock.ANY, mock.ANY)]
        self.network.set.assert_has_calls(calls)

    def test_setup_for_pip_local(self):
        self.cmd.onecmd('setup_for_pip_local repo')
        calls = [mock.call.set('repo', mock.ANY, mock.ANY)]
        self.network.set.assert_has_calls(calls)

    def test_serve(self):
        self.cmd.onecmd('serve repo1')
        self.repo1.serve.assert_called_once_with()

    def test_network_reload_called_before_every_command_in_the_loop(self):
        self.network.repo_names = ['repo-a']
        with fake_stdin('\nlist\n'):
            self.cmd.cmdloop()

        self.assertEqual(
            [
                mock.call.reload(),  # empty line
                mock.call.reload(),  # list
                mock.call.reload(),  # EOF
            ], self.network.mock_calls
        )
