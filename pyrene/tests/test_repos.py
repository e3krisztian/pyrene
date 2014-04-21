# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import mock
from io import StringIO
import pyrene.repos as m
from pyrene.constants import REPO, REPOTYPE
from .util import capture_stdout, Assertions


class Test_BadRepo(unittest.TestCase):

    def setUp(self):
        self.repo = m.BadRepo('repo', {})

    def test_download_package(self):
        self.repo.download_packages('a', '.')

    def test_upload_packages(self):
        self.repo.upload_packages(['a'])


class Test_DirectoryRepo(Assertions, unittest.TestCase):

    def make_repo(self, attrs, name='repo'):
        return m.DirectoryRepo(name, attrs)

    def test_attributes(self):
        repo = self.make_repo({'directory': 'dir@', 'type': 'directory'})
        self.assertEqual('directory', repo.type)
        self.assertEqual('dir@', repo.directory)

    def test_incomplete_repo_get_as_pip_conf(self):
        repo = self.make_repo({})
        with self.assertRaises(AttributeError):
            repo.get_as_pip_conf()

    def test_get_as_pip_conf(self):
        directory = '/path/to/repo'
        repo = self.make_repo({REPO.DIRECTORY: directory})
        self.assertIn(directory, repo.get_as_pip_conf())

    def test_serve_without_upload_user(self):
        attrs = {REPO.TYPE: REPOTYPE.DIRECTORY, REPO.DIRECTORY: '.'}
        repo = self.make_repo(attrs)
        pypi = mock.Mock()
        repo.serve(pypi)

    def test_serve_with_upload_user(self):
        attrs = {
            REPO.TYPE: REPOTYPE.DIRECTORY,
            REPO.DIRECTORY: '.',
            REPO.SERVE_USERNAME: 'tu',
            REPO.SERVE_PASSWORD: 'tp',
        }
        repo = self.make_repo(attrs)
        pypi = mock.Mock()
        repo.serve(pypi)

    def test_print_attributes(self):
        with capture_stdout() as stdout:
            self.make_repo({}).print_attributes()
            output = stdout.content

        self.assertContainsInOrder(output, m.DirectoryRepo.ATTRIBUTES)
        self.assertNotIn(REPO.DOWNLOAD_URL, output)


class Test_HttpRepo(Assertions, unittest.TestCase):

    def make_repo(self, attrs, name='repo'):
        return m.HttpRepo(name, attrs)

    def test_attributes(self):
        repo = self.make_repo(
            {
                REPO.DOWNLOAD_URL: 'https://priv.repos.org/simple',
                REPO.TYPE: REPOTYPE.HTTP
            }
        )
        self.assertEqual('http', repo.type)
        self.assertEqual('https://priv.repos.org/simple', repo.download_url)

    def test_serve(self):
        repo = self.make_repo(
            {
                REPO.DOWNLOAD_URL: 'https://priv.repos.org/simple',
            }
        )
        with mock.patch('sys.stdout', new_callable=StringIO) as stdout:
            repo.serve()

            self.assertIn('https://priv.repos.org/simple', stdout.getvalue())

    def test_incomplete_repo_get_as_pip_conf(self):
        repo = self.make_repo({})
        with self.assertRaises(AttributeError):
            repo.get_as_pip_conf()

    def test_get_as_pip_conf(self):
        url = 'http://download/url'
        repo = self.make_repo({REPO.DOWNLOAD_URL: url})
        self.assertIn(url, repo.get_as_pip_conf())

    def test_print_attributes(self):
        with capture_stdout() as stdout:
            self.make_repo({}).print_attributes()
            output = stdout.content

        self.assertContainsInOrder(output, m.HttpRepo.ATTRIBUTES)
        self.assertNotIn(REPO.DIRECTORY, output)
