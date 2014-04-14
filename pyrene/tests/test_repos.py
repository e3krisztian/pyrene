# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import mock
from io import StringIO
import pyrene.repos as m


class Test_DirectoryRepo(unittest.TestCase):

    def test_attributes(self):
        repo = m.DirectoryRepo({'directory': 'dir@', 'type': 'directory'})
        self.assertEqual('directory', repo.type)
        self.assertEqual('dir@', repo.directory)

    def test_incomplete_repo_get_as_pip_conf(self):
        repo = m.DirectoryRepo({})
        pip_conf = repo.get_as_pip_conf()

        self.assertIn('find-links', pip_conf)


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
