# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import pyrene.util as m
from .util import capture_stdout
import unittest

import os
import subprocess
from temp_dir import within_temp_dir

from tempfile import NamedTemporaryFile
from passlib.apache import HtpasswdFile


class Test_set_env(unittest.TestCase):

    def setUp(self):
        self.original_environ = os.environ.copy()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_environ)

    def test_overwrite_existing_key(self):
        os.environ['existing'] = '1'

        with m.set_env('existing', '2'):
            self.assertEqual('2', os.environ['existing'])

        self.assertEqual('1', os.environ['existing'])

    def test_make_new_key(self):
        if 'new' in os.environ:
            del os.environ['new']

        with m.set_env('new', '2'):
            self.assertEqual('2', os.environ['new'])

        self.assertNotIn('new', os.environ)


TEST_SETUP_PY = '''\
from distutils.core import setup

setup(
    name='foo',
    version='1.0',
    py_modules=['foo'],
)
'''


class Test_pip_install(unittest.TestCase):

    @within_temp_dir
    def test_copy_package(self):
        m.write_file('setup.py', TEST_SETUP_PY)
        m.write_file('foo.py', '')
        subprocess.check_output(
            'python setup.py sdist'.split(),
            stderr=subprocess.STDOUT
        )
        os.mkdir('destination')

        with capture_stdout() as stdout:
            m.pip_install(
                '--download', 'destination',
                '--find-links', 'dist',
                '--no-index',
                'foo',
            )
            output = stdout.content

        # diagnostic - in case pip has failed
        print(output)

        self.assertTrue(os.path.exists('destination/foo-1.0.tar.gz'))


class Test_Directory(unittest.TestCase):

    @within_temp_dir
    def test_files(self):
        os.makedirs('a/directory')
        d = m.Directory('a')
        m.write_file('a/file1', '')
        m.write_file('a/file2', '')

        f1 = os.path.join('a', 'file1')
        f2 = os.path.join('a', 'file2')
        self.assertEqual([f1, f2], d.files)

    @within_temp_dir
    def test_clear(self):
        os.makedirs('a/directory')
        d = m.Directory('a')
        m.write_file('a/file1', '')
        m.write_file('a/file2', '')

        d.clear()

        self.assertEqual([], d.files)


class Test_make_htpasswd(unittest.TestCase):

    def test(self):
        with NamedTemporaryFile() as file:
            m.make_htpasswd(file.name, 'testuser', 'testpass')

            ht = HtpasswdFile(file.name)
            self.assertEqual(['testuser'], ht.users())
            self.assertTrue(ht.check_password('testuser', 'testpass'))


class Test_generate_password(unittest.TestCase):

    def test_non_repeating(self):
        passwords = [m.generate_password() for _ in range(1000)]
        self.assertEqual(len(set(passwords)), len(passwords))
