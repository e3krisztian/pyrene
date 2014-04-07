# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import reponet.repos as m


class Test_FileRepo(unittest.TestCase):

    def test_attributes(self):
        repo = m.FileRepo({'directory': 'dir@', 'type': 'file'})
        self.assertEqual('file', repo.type)
        self.assertEqual('dir@', repo.directory)


class Test_HttpRepo(unittest.TestCase):

    def test_attributes(self):
        repo = m.FileRepo(
            {
                'download_url': 'https://priv.repos.org/simple',
                'type': 'http'
            }
        )
        self.assertEqual('http', repo.type)
        self.assertEqual('https://priv.repos.org/simple', repo.download_url)
