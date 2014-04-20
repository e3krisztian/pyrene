# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import mock
from io import StringIO
import pyrene.repos as m
from pyrene.constants import REPO, REPOTYPE


class Test_NullRepo(unittest.TestCase):

    def setUp(self):
        self.repo = m.NullRepo({})

    def test_download_package(self):
        self.repo.download_packages('a', '.')

    def test_upload_packages(self):
        self.repo.upload_packages(['a'])


class Test_DirectoryRepo(unittest.TestCase):

    def test_attributes(self):
        repo = m.DirectoryRepo({'directory': 'dir@', 'type': 'directory'})
        self.assertEqual('directory', repo.type)
        self.assertEqual('dir@', repo.directory)

    def test_incomplete_repo_get_as_pip_conf(self):
        repo = m.DirectoryRepo({})
        pip_conf = repo.get_as_pip_conf()

        self.assertIn('find-links', pip_conf)

    def test_serve_without_upload_user(self):
        attrs = {REPO.TYPE: REPOTYPE.DIRECTORY, REPO.DIRECTORY: '.'}
        repo = m.DirectoryRepo(attrs)
        pypi = mock.Mock()
        repo.serve(pypi)

    def test_serve_with_upload_user(self):
        attrs = {
            REPO.TYPE: REPOTYPE.DIRECTORY,
            REPO.DIRECTORY: '.',
            REPO.SERVE_USERNAME: 'tu',
            REPO.SERVE_PASSWORD: 'tp',
        }
        repo = m.DirectoryRepo(attrs)
        pypi = mock.Mock()
        repo.serve(pypi)


class Test_HttpRepo(unittest.TestCase):

    def test_attributes(self):
        repo = m.HttpRepo(
            {
                'download_url': 'https://priv.repos.org/simple',
                'type': 'http'
            }
        )
        self.assertEqual('http', repo.type)
        self.assertEqual('https://priv.repos.org/simple', repo.download_url)

    def test_serve(self):
        repo = m.HttpRepo(
            {
                'download_url': 'https://priv.repos.org/simple',
            }
        )
        with mock.patch('sys.stdout', new_callable=StringIO) as stdout:
            repo.serve()

            self.assertIn('https://priv.repos.org/simple', stdout.getvalue())

    def test_incomplete_repo_get_as_pip_conf(self):
        repo = m.HttpRepo({})
        pip_conf = repo.get_as_pip_conf()

        self.assertIn('localhost', pip_conf)
