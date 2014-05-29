# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import pyrene.util as m
from .util import capture_stdout
import unittest

import os
import subprocess
import mock
from temp_dir import within_temp_dir

from tempfile import NamedTemporaryFile
from passlib.apache import HtpasswdFile


class Test_set_env(unittest.TestCase):

    def setUp(self):
        self.original_environ = os.environ.copy()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_environ)

    def test_overwrite_existing_variable(self):
        os.environ['existing'] = '1'

        with m.set_env('existing', '2'):
            self.assertEqual('2', os.environ['existing'])

        self.assertEqual('1', os.environ['existing'])

    def test_make_new_variable(self):
        if 'new' in os.environ:
            del os.environ['new']

        with m.set_env('new', '2'):
            self.assertEqual('2', os.environ['new'])

        self.assertNotIn('new', os.environ)


TEST_SETUP_PY = b'''\
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
        m.write_file('foo.py', b'')
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
        m.write_file('a/file1', b'')
        m.write_file('a/file2', b'')

        f1 = os.path.join('a', 'file1')
        f2 = os.path.join('a', 'file2')
        self.assertEqual([f1, f2], d.files)

    @within_temp_dir
    def test_clear(self):
        os.makedirs('a/directory')
        d = m.Directory('a')
        m.write_file('a/file1', b'')
        m.write_file('a/file2', b'')

        d.clear()

        self.assertEqual([], d.files)


class Test_generate_password(unittest.TestCase):

    def test_non_repeating(self):
        passwords = [m.generate_password() for _ in range(1000)]
        self.assertEqual(len(set(passwords)), len(passwords))


class Test_PyPI(unittest.TestCase):

    def setUp(self):
        self.server = m.PyPI()
        self.server.execute = mock.Mock()

    @property
    def executed_cmd(self):
        ARGS_LIST = 1
        return self.server.execute.mock_calls[0][ARGS_LIST][0]

    def test_serve_volatile(self):
        self.server.volatile = True
        self.server.serve()
        self.assertIn('--overwrite', self.executed_cmd)

    def test_serve_non_volatile(self):
        self.server.serve()
        self.assertNotIn('--overwrite', self.executed_cmd)

    def test_make_htpasswd(self):
        self.server.add_user('testuser', 'testpass')
        self.server.add_user('xtestuser', 'xtestpass')
        with NamedTemporaryFile() as file:
            self.server.make_htpasswd(file.name)

            ht = HtpasswdFile(file.name)
            self.assertEqual(['testuser', 'xtestuser'], sorted(ht.users()))
            self.assertTrue(ht.check_password('testuser', 'testpass'))

    def test_serve_with_credentials(self):
        self.server.add_user('u', 'p')
        self.server.serve()
        self.assertIn('--passwords', self.executed_cmd)

    def test_serve_no_user(self):
        self.server.serve()
        self.assertNotIn('--passwords', self.executed_cmd)


class Test_create_md5_backup(unittest.TestCase):

    @within_temp_dir
    def test(self):
        SOMECONTENT = b'sometext'
        m.write_file('file', SOMECONTENT)

        m.create_md5_backup('file')

        with open('file.a29e90948f4eee52168fab5fa9cfbcf8', 'rb') as f:
            content = f.read()
        self.assertEqual(SOMECONTENT, content)
