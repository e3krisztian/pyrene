# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import pyrene.network as m
import unittest

import os
import tempfile
from temp_dir import within_temp_dir
from pyrene.util import write_file
from pyrene.constants import REPO, REPOTYPE
from pyrene.repos import Repo


class Test_Network_create(unittest.TestCase):

    @within_temp_dir
    def test_missing_repo_store_define_creates_it(self):
        network = m.Network('repo_store')
        network.define('repo')

        self.assertTrue(os.path.isfile('repo_store'))


class Test_Network(unittest.TestCase):

    def setUp(self):
        fd, self.repo_store = tempfile.mkstemp()
        os.close(fd)
        self.network = m.Network(self.repo_store)

    def tearDown(self):
        os.remove(self.repo_store)

    def test_get_repo_fails_on_undefined_repo(self):
        with self.assertRaises(m.UnknownRepoError):
            self.network.get_repo('undefined')

    def test_get_repo_returns_badrepo_on_missing_repo_type(self):
        self.network.define('no-type')
        self.network.set('no-type', 'attr', 'attr-value')
        repo = self.network.get_repo('no-type')
        self.assertIsInstance(repo, m.BadRepo)
        self.assertEqual('attr-value', repo.attr)

    def test_get_repo_returns_repo(self):
        self.network.define('repo')
        self.network.set('repo', 'type', 'http')
        repo = self.network.get_repo('repo')
        self.assertIsInstance(repo, Repo)

    def test_get_repo_fails_on_unknown_repo_type(self):
        self.network.define('repo')
        self.network.set('repo', 'type', 'unknown!')
        repo = self.network.get_repo('repo')
        self.assertIsInstance(repo, m.BadRepo)

    def test_get_repo_sets_repo_name(self):
        self.network.define('r!')
        repo = self.network.get_repo('r!')
        self.assertEqual('r!', repo.name)

    def test_get_repo_with_empty_repo_name_returns_active_repo(self):
        self.network.define('activerepo')
        self.network.set('activerepo', 'type', 'http')
        self.network.active_repo = 'activerepo'

        repo = self.network.get_repo('')

        self.assertEqual('activerepo', repo.name)

    def make_file_repo(self, directory):
        self.network.define('repo')
        self.network.set('repo', REPO.TYPE, REPOTYPE.DIRECTORY)
        self.network.set('repo', REPO.DIRECTORY, directory)

    def test_directory_is_available_on_file_repo(self):
        self.make_file_repo('/a/repo/dir')

        repo = self.network.get_repo('repo')
        self.assertEqual('/a/repo/dir', repo.directory)

    def test_set_is_persistent(self):
        self.make_file_repo('/a/repo/dir')

        other_network = m.Network(self.repo_store)
        repo = other_network.get_repo('repo')
        self.assertEqual('/a/repo/dir', repo.directory)

    def test_unset_is_persistent(self):
        self.make_file_repo('/a/repo/dir')
        self.network.unset('repo', REPO.DIRECTORY)

        other_network = m.Network(self.repo_store)
        repo = other_network.get_repo('repo')
        with self.assertRaises(AttributeError):
            repo.directory
        # self.assertEqual('/a/repo/dir', repo.directory)

    def test_forget_is_persistent(self):
        self.make_file_repo('/a/repo/dir')
        self.network.forget('repo')

        other_network = m.Network(self.repo_store)
        with self.assertRaises(m.UnknownRepoError):
            other_network.get_repo('repo')

    def test_repo_names(self):
        self.network.define('r1')
        self.network.define('r4')
        self.assertEqual({'r1', 'r4'}, set(self.network.repo_names))

    def test_get_attributes(self):
        self.network.define('r1')
        self.network.set('r1', 'ame', '2')
        self.network.set('r1', 'nme', '22')
        self.network.define('r2')
        self.network.set('r2', 'name', 'fixed')

        self.assertDictEqual(
            {'ame': '2', 'nme': '22'},
            self.network.get_attributes('r1')
        )
        self.assertDictEqual(
            {'name': 'fixed'},
            self.network.get_attributes('r2')
        )

    def test_get_attributes_on_undefined_repo(self):
        with self.assertRaises(m.UnknownRepoError):
            self.network.get_attributes('undefined-repo')


TEST_CONFIG = b'''\
[repo:1]
type=directory
directory=/tmp
'''

# https://docs.python.org/2/distutils/packageindex.html#pypirc
A_PYPIRC = b'''\
[distutils]
index-servers =
    pypi
    other

[pypi]
repository: <repository-url>
username: <username>

[other]
password: <password>
'''


class Test_Network_dot_pyrene(unittest.TestCase):

    def setUp(self):
        fd, self.repo_store = tempfile.mkstemp()
        os.close(fd)
        self.network = m.Network(self.repo_store)

    def tearDown(self):
        os.remove(self.repo_store)

    def test_reload(self):
        self.network.define('repo')

        write_file(self.repo_store, TEST_CONFIG)
        self.network.reload()

        self.assertEqual(['1'], self.network.repo_names)

    def test_import_pypirc(self):
        fd, pypirc = tempfile.mkstemp()
        os.close(fd)
        try:
            write_file(pypirc, A_PYPIRC)
            self.network.import_pypirc(pypirc)
        finally:
            os.remove(pypirc)

        # reload - to show imported pypirc is persistent
        self.network.reload()

        self.assertEqual(set(['pypi', 'other']), set(self.network.repo_names))
        pypi = self.network.get_repo('pypi')
        self.assertEqual('http', pypi.type)
        self.assertEqual('<repository-url>', pypi.upload_url)
        self.assertEqual('<username>', pypi.username)
        other = self.network.get_repo('other')
        self.assertEqual('<password>', other.password)
