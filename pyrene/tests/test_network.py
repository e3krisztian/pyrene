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

    def test_get_repo_returns_nullrepo_on_missing_repo_type(self):
        self.network.define('no-type')
        self.network.set('no-type', 'attr', 'attr-value')
        repo = self.network.get_repo('no-type')
        self.assertIsInstance(repo, m.NullRepo)
        self.assertEqual('attr-value', repo.attr)

    def test_get_repo_returns_repo(self):
        self.network.define('repo')
        self.network.set('repo', 'type', 'http')
        repo = self.network.get_repo('repo')
        self.assertIsInstance(repo, Repo)

    def test_get_repo_fails_on_unknown_repo_type(self):
        self.network.define('repo')
        self.network.set('repo', 'type', 'unknown!')
        with self.assertRaises(m.UnknownRepoType):
            self.network.get_repo('repo')

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


TEST_CONFIG = '''\
[repo:1]
type=directory
directory=/tmp
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
