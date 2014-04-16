# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import pyrene.network as m
import unittest

import os
import tempfile
from temp_dir import within_temp_dir

from pyrene.repos import Repo


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
        self.repo_manager.set('repo', 'type', 'http')
        repo = self.repo_manager.get_repo('repo')
        self.assertIsInstance(repo, Repo)

    def test_get_repo_fails_on_unknown_repo_type(self):
        self.repo_manager.define('repo')
        self.repo_manager.set('repo', 'type', 'unknown!')
        with self.assertRaises(m.UnknownRepoType):
            self.repo_manager.get_repo('repo')

    def make_file_repo(self, directory):
        self.repo_manager.define('repo')
        self.repo_manager.set('repo', 'type', m.REPOTYPE_DIRECTORY)
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
