# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import shutil
import sys

import unittest
import mock
import paix as m


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


def write_file(path, content):
    with open(path, 'wb') as file:
        file.write(content)


def read_file(path):
    with open(path, 'rb') as file:
        return file.read()


class Test_Paix(unittest.TestCase):

    def setUp(self):
        self.repo1 = mock.Mock(spec_set=m.Repo)
        self.repo2 = mock.Mock(spec_set=m.Repo)
        self.somerepo = mock.Mock(spec_set=m.Repo)
        self.repo_manager = mock.Mock(spec_set=m.RepoManager)
        self.repo_manager.get_repo.configure_mock(side_effect=self.get_repo)
        self.directory = mock.Mock(spec_set=m.Directory)
        self.paix = m.Paix(
            repo_manager=self.repo_manager,
            directory=self.directory
        )
        self.paix.write_file = mock.Mock()

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

        self.paix.onecmd('use somerepo')

        self.somerepo.get_as_pip_conf.assert_called_once_with()
        self.paix.write_file.assert_called_once_with(
            '~/.pip/pip.conf',
            mock.sentinel.pip_conf
        )

    def test_copy_single_package(self):
        self.directory.files = ['roman-2.0.0.zip']

        self.paix.onecmd('copy repo1:roman==2.0.0 repo2:')

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

        self.paix.onecmd('copy repo1:roman==2.0.0 repo2:')

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

        self.paix.onecmd('copy repo1:roman==2.0.0 repo2:')

        self.repo1.download_packages.assert_called_once_with(
            'roman==2.0.0',
            self.directory
        )

    def test_copy_uses_repo_to_upload_packages(self):
        self.directory.files = ['roman-2.0.0.zip']

        self.paix.onecmd('copy repo1:roman==2.0.0 repo2:')

        self.repo2.upload_packages.assert_called_once_with(['roman-2.0.0.zip'])

    def test_copy_package_with_dependencies(self):
        package_files = ('pkg-1.0.0.tar.gz', 'dep-0.3.1.zip')
        self.directory.files = list(package_files)

        self.paix.onecmd('copy repo1:pkg repo2:')

        self.repo1.download_packages.assert_called_once_with(
            'pkg',
            self.directory
        )
        self.repo2.upload_packages.assert_called_once_with(list(package_files))

    def test_copy_from_two_repos(self):
        package_files = ('a-1.egg', 'b-2.tar.gz')
        self.directory.files = list(package_files)

        self.paix.onecmd('copy repo1:a repo2:b somerepo:')

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

    @unittest.skip('TODO')
    def test_define(self):
        self.paix.onecmd('define new-repo')

    @unittest.skip('TODO')
    def test_drop(self):
        self.paix.onecmd('drop repo1')

    @unittest.skip('TODO')
    def test_configure(self):
        # file repos:
        self.paix.onecmd('configure repo1 type file')
        self.paix.onecmd('configure repo1 directory ')

        # http repos:
        self.paix.onecmd('configure repo1 type http')
        self.paix.onecmd('configure repo1 download-url http://...')
        self.paix.onecmd('configure repo1 upload-url http://...')
        self.paix.onecmd('configure repo1 username user')
        self.paix.onecmd('configure repo1 password pass')

        # specials:
        self.paix.onecmd('configure repo1 type python')
        self.paix.onecmd('configure repo1 type piplocal')
