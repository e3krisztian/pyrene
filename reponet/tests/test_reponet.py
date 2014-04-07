# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import os
import shutil
import sys
from io import StringIO

import unittest
import mock
from temp_dir import within_temp_dir
import tempfile

import reponet.main as m
from reponet.repos import Repo

# START: unique_justseen
# https://docs.python.org/2.7/library/itertools.html#itertools-recipes
from itertools import imap, groupby
from operator import itemgetter


def unique_justseen(iterable, key=None):
    '''List unique elements, preserving order.

    Remember only the element just seen.
    '''
    return map(next, imap(itemgetter(1), groupby(iterable, key)))

assert unique_justseen('AAAABBBCCDAABBB') == list('ABCDAB')
assert unique_justseen('ABBCcAD', unicode.lower) == list('ABCAD')

# END: unique_justseen


def rmtree(dir):
    if dir:
        try:
            shutil.rmtree(dir)
        except:
            sys.stderr.write('could not remove {}'.format(dir))


write_file = m.write_file


def read_file(path):
    with open(path, 'rb') as file:
        return file.read()


class Test_RepoManager_create(unittest.TestCase):

    @within_temp_dir
    def test_missing_repo_store_define_creates_it(self):
        repo_manager = m.RepoManager('repo_store')
        repo_manager.define('repo')

        self.assertTrue(os.path.isfile('repo_store'))


class Test_RepoManager(unittest.TestCase):

    def setUp(self):
        fd, self.repo_store = tempfile.mkstemp()
        os.close(fd)
        self.repo_manager = m.RepoManager(self.repo_store)

    def tearDown(self):
        os.remove(self.repo_store)

    def test_get_repo_fails_on_undefined_repo(self):
        with self.assertRaises(m.UnknownRepoError):
            self.repo_manager.get_repo('undefined')

    def test_get_repo_fails_on_missing_repo_type(self):
        self.repo_manager.define('no-type')
        with self.assertRaises(m.UndefinedRepoType):
            self.repo_manager.get_repo('no-type')

    def test_get_repo_returns_repo(self):
        self.repo_manager.define('repo')
        self.repo_manager.set('repo', 'type', 'pypi')
        repo = self.repo_manager.get_repo('repo')
        self.assertIsInstance(repo, Repo)

    def test_get_repo_fails_on_unknown_repo_type(self):
        self.repo_manager.define('repo')
        self.repo_manager.set('repo', 'type', 'unknown!')
        with self.assertRaises(m.UnknownRepoType):
            self.repo_manager.get_repo('repo')

    def make_file_repo(self, directory):
        self.repo_manager.define('repo')
        self.repo_manager.set('repo', 'type', m.REPOTYPE_FILE)
        self.repo_manager.set('repo', 'directory', directory)

    def test_directory_is_available_on_file_repo(self):
        self.make_file_repo('/a/repo/dir')

        repo = self.repo_manager.get_repo('repo')
        self.assertEqual('/a/repo/dir', repo.directory)

    def test_set_is_persistent(self):
        self.make_file_repo('/a/repo/dir')

        other_repo_manager = m.RepoManager(self.repo_store)
        repo = other_repo_manager.get_repo('repo')
        self.assertEqual('/a/repo/dir', repo.directory)

    def test_forget_is_persistent(self):
        self.make_file_repo('/a/repo/dir')
        self.repo_manager.forget('repo')

        other_repo_manager = m.RepoManager(self.repo_store)
        with self.assertRaises(m.UnknownRepoError):
            other_repo_manager.get_repo('repo')

    def test_repo_names(self):
        self.repo_manager.define('r1')
        self.repo_manager.define('r4')
        self.assertEqual({'r1', 'r4'}, set(self.repo_manager.repo_names))

    def test_get_attributes(self):
        self.repo_manager.define('r1')
        self.repo_manager.set('r1', 'ame', '2')
        self.repo_manager.set('r1', 'nme', '22')
        self.repo_manager.define('r2')
        self.repo_manager.set('r2', 'name', 'fixed')

        self.assertDictEqual(
            {'ame': '2', 'nme': '22'},
            self.repo_manager.get_attributes('r1')
        )
        self.assertDictEqual(
            {'name': 'fixed'},
            self.repo_manager.get_attributes('r2')
        )


class Test_RepoNetCmd_write_file(unittest.TestCase):

    def setUp(self):
        self.repo_manager = mock.Mock(spec_set=m.RepoManager)
        self.directory = mock.Mock(spec_set=m.Directory)
        self.cmd = m.RepoNetCmd(
            repo_manager=self.repo_manager,
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


class Test_RepoNetCmd(unittest.TestCase):

    def setUp(self):
        self.repo1 = mock.Mock(spec_set=Repo)
        self.repo2 = mock.Mock(spec_set=Repo)
        self.somerepo = mock.Mock(spec_set=Repo)
        self.repo_manager = mock.Mock(spec_set=m.RepoManager)
        self.repo_manager.get_repo.configure_mock(side_effect=self.get_repo)
        self.directory = mock.Mock(spec_set=m.Directory)
        self.cmd = m.RepoNetCmd(
            repo_manager=self.repo_manager,
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

    def test_use(self):
        self.somerepo.get_as_pip_conf.configure_mock(
            return_value=mock.sentinel.pip_conf
        )

        self.cmd.onecmd('use somerepo')

        self.somerepo.get_as_pip_conf.assert_called_once_with()
        self.cmd.write_file.assert_called_once_with(
            os.path.expanduser('~/.pip/pip.conf'),
            mock.sentinel.pip_conf
        )

    def test_copy_single_package(self):
        self.directory.files = ['roman-2.0.0.zip']

        self.cmd.onecmd('copy repo1:roman==2.0.0 repo2:')

        self.assertEqual(
            unique_justseen(
                sorted(
                    [
                        mock.call.get_repo('repo1'),
                        mock.call.get_repo('repo2'),
                    ]
                )
            ),
            unique_justseen(sorted(self.repo_manager.mock_calls))
        )

        self.repo1.download_packages.assert_called_once_with(
            'roman==2.0.0',
            self.directory
        )
        self.repo2.upload_packages.assert_called_once_with(['roman-2.0.0.zip'])

    def test_copy_uses_repo_manager(self):
        self.directory.files = ['roman-2.0.0.zip']

        self.cmd.onecmd('copy repo1:roman==2.0.0 repo2:')

        self.assertEqual(
            unique_justseen(
                sorted(
                    [
                        mock.call.get_repo('repo1'),
                        mock.call.get_repo('repo2'),
                    ]
                )
            ),
            unique_justseen(sorted(self.repo_manager.mock_calls))
        )

    def test_copy_uses_repo_to_download_packages(self):
        self.directory.files = ['roman-2.0.0.zip']

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

    def test_define(self):
        self.cmd.onecmd('define new-repo')

        self.repo_manager.define.assert_called_once_with('new-repo')

    def test_forget(self):
        self.cmd.onecmd('forget somerepo')

        self.repo_manager.forget.assert_called_once_with('somerepo')

    def test_set(self):
        self.cmd.onecmd('set repo1 key=value')

        self.repo_manager.set.assert_called_once_with('repo1', 'key', 'value')

    def test_list(self):
        self.repo_manager.repo_names = ['S1', '#@!']

        with mock.patch('sys.stdout', new_callable=StringIO) as stdout:
            self.cmd.onecmd('list')

            self.assertIn('S1', stdout.getvalue())
            self.assertIn('#@!', stdout.getvalue())

    def test_show(self):
        self.repo_manager.get_attributes.configure_mock(
            return_value={'name': 'SHRP1', m.KEY_TYPE: '??'}
        )
        with mock.patch('sys.stdout', new_callable=StringIO) as stdout:
            self.cmd.onecmd('show repo1')

            self.assertEqual(
                [mock.call.get_attributes('repo1')],
                self.repo_manager.mock_calls
            )
            output = stdout.getvalue()
            self.assertRegexpMatches(output, '.*name.*SHRP1.*')
            self.assertRegexpMatches(output, '.*type.*[?][?].*')

    def test_complete_set_before_repo(self):
        self.repo_manager.repo_names = ('repo', 'repo2')
        completion = self.cmd.complete_set('', 'set re key=value', 4, 4)
        self.assertEqual({'repo ', 'repo2 '}, set(completion))

    def test_complete_set_on_repo(self):
        self.repo_manager.repo_names = ('repo', 'repo2')
        completion = self.cmd.complete_set('re', 'set re key=value', 4, 5)
        self.assertEqual({'repo ', 'repo2 '}, set(completion))

    def test_complete_set_on_key(self):
        completion = self.cmd.complete_set('', 'set re key=value', 7, 7)
        self.assertEqual(set(m.REPO_ATTRIBUTE_COMPLETIONS), set(completion))

    def test_complete_set_on_key_ty(self):
        completion = self.cmd.complete_set('ty', 'set re ty=value', 7, 9)
        self.assertEqual({'type='}, set(completion))

    def test_complete_set_on_type_value_fi(self):
        completion = self.cmd.complete_set(
            'fi',
            'set re type=fi',
            12,
            14,
        )
        self.assertEqual(['file'], completion)

    def test_complete_set_on_empty_type_value(self):
        completion = self.cmd.complete_set(
            '',
            'set re type=',
            12,
            12,
        )
        self.assertEqual(set(m.TYPE_TO_CLASS), set(completion))

    def test_complete_set_on_value(self):
        completion = self.cmd.complete_set('key=', 'set re key=value', 7, 11)
        self.assertEqual(set(), set(completion))
