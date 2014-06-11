# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import mock
import os
from temp_dir import within_temp_dir

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
        attrs = attrs.copy()
        attrs[REPO.TYPE] = REPOTYPE.DIRECTORY
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
        repo = self.make_repo({REPO.DIRECTORY: '.'})
        pypi = mock.Mock()
        repo.serve(pypi)

    def test_serve_with_upload_user(self):
        attrs = {
            REPO.DIRECTORY: '.',
            REPO.SERVE_USERNAME: 'tu',
            REPO.SERVE_PASSWORD: 'tp',
        }
        repo = self.make_repo(attrs)
        pypi = mock.Mock()
        repo.serve(pypi)

    @within_temp_dir
    def test_serve_creates_nonexistent_repo_directory(self):
        repo = self.make_repo({REPO.DIRECTORY: 'missing'})
        pypi = mock.Mock()

        repo.serve(pypi)

        self.assertTrue(os.path.isdir('missing'))

    @within_temp_dir
    def test_upload_packages_creates_nonexistent_repo_directory(self):
        repo = self.make_repo({REPO.DIRECTORY: 'missing'})

        repo.upload_packages([])

        self.assertTrue(os.path.isdir('missing'))

    def test_print_attributes(self):
        with capture_stdout() as stdout:
            self.make_repo({}).print_attributes()
            output = stdout.content

        self.assertContainsInOrder(output, m.DirectoryRepo.ATTRIBUTES)
        self.assertNotIn(REPO.DOWNLOAD_URL, output)


class Test_HttpRepo(Assertions, unittest.TestCase):

    def make_repo(self, attrs, name='repo'):
        attrs = attrs.copy()
        attrs[REPO.TYPE] = REPOTYPE.HTTP
        return m.HttpRepo(name, attrs)

    def test_attributes(self):
        repo = self.make_repo(
            {REPO.DOWNLOAD_URL: 'https://priv.repos.org/simple'}
        )
        self.assertEqual('http', repo.type)
        self.assertEqual('https://priv.repos.org/simple', repo.download_url)

    def test_serve(self):
        repo = self.make_repo(
            {REPO.DOWNLOAD_URL: 'https://priv.repos.org/simple'}
        )

        with capture_stdout() as stdout:
            repo.serve()
            output = stdout.content

        self.assertIn('https://priv.repos.org/simple', output)

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

    def test_upload_continues_after_UploadError(self):
        repo = self.make_repo(
            {
                REPO.UPLOAD_URL: 'example.com',
                REPO.SERVE_USERNAME: 'index owner',
                REPO.SERVE_PASSWORD: 'password',
            }
        )

        call_args = []

        class Uploader(m.BaseUploader):
            def upload(self, package_file):
                call_args.append(package_file)
                raise m.UploadError(package_file)
        repo.get_uploader = mock.Mock(
            repo.get_uploader,
            side_effect=[Uploader(repo)]
        )
        with capture_stdout() as stdout:
            repo.upload_packages(['file1', 'file2', 'file3'])
            output = stdout.content

        self.assertEqual(call_args, ['file1', 'file2', 'file3'])
        self.assertContainsInOrder(
            output,
            ['There was an error', 'upload', 'file'] * 3
        )
