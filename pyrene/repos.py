# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import abc
import os
import sys
import shutil
import subprocess
import tempfile
from .util import set_env, write_file, print_command
from .util import pip_install, PyPI, red, green, yellow, bold
from .constants import REPO


class UploadError(Exception):

    def __init__(self, package_file):
        self.package_file = package_file
        self.package_name = os.path.basename(package_file)

    def __str__(self):
        return (
            'There was an error during upload of {}'
            .format(self.package_name)
        )


class BaseUploader(object):

    def __init__(self, repository):
        self.repository = repository.name

    def __enter__(self):
        return self.upload

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def upload(self, package_file):
        pass


class Repo(object):
    __metaclass__ = abc.ABCMeta

    ATTRIBUTES = (REPO.TYPE,)
    DEFAULTS = {}
    UPLOADER = BaseUploader
    attributes = dict

    def __init__(self, name, attributes):
        super(Repo, self).__init__()
        self.name = name
        self.attributes = dict(attributes)

    def __getattr__(self, attribute):
        try:
            return self.attributes[attribute]
        except KeyError:
            try:
                return self.DEFAULTS[attribute]
            except KeyError:
                raise AttributeError(attribute)

    @abc.abstractmethod
    def get_as_pip_conf(self):
        pass

    @abc.abstractmethod
    def download_packages(self, package_spec, directory):
        pass

    def get_uploader(self):
        return self.UPLOADER(self)

    def upload_packages(self, package_files):
        with self.get_uploader() as upload:
            for package_file in package_files:
                pkg_name = os.path.basename(package_file)

                msg = ' * Uploading {} to {}'.format(pkg_name, self.name)
                print(bold(msg))

                try:
                    upload(package_file)
                    print(green(' * OK'))
                except UploadError as e:
                    print(bold(red(' * {}'.format(e))))

    @abc.abstractmethod
    def serve(self):
        pass

    def print_attributes(self):
        def comment(text, color):
            return '# {}'.format(color(text))
        for attribute in self.ATTRIBUTES:
            if attribute in self.attributes:
                msg = (
                    '{} = {}'
                    .format(attribute, self.attributes[attribute])
                )
            elif attribute in self.DEFAULTS:
                msg = (
                    '# {} = {}'
                    .format(attribute, self.DEFAULTS[attribute])
                )
            else:
                msg = comment(attribute, yellow)

            print(msg)

        extra_attrs = sorted(
            set(self.attributes.keys()) - set(self.ATTRIBUTES)
        )
        if extra_attrs:
            print()
            print(comment('EXTRA ATTRIBUTES >>>', red))
            for attribute in extra_attrs:
                msg = '{} = {}'.format(attribute, self.attributes[attribute])
                print(msg)
            print(comment('<<< EXTRA ATTRIBUTES', red))


PIPCONF_BADREPO = '''\
[global]
# no package can be installed from a BadRepo
no-index = true
'''


class BadRepo(Repo):

    ATTRIBUTES = {}
    DEFAULTS = {}

    def get_as_pip_conf(self):
        return PIPCONF_BADREPO

    @property
    def printable_name(self):
        return red('{} (a misconfigured repo!)'.format(self.name))

    def download_packages(self, package_spec, directory):
        print(
            '{}: pretended to provide package "{}"'
            .format(self.printable_name, package_spec)
        )

    def upload_packages(self, package_files):
        if package_files:
            print(
                '{}: pretended to upload package files'
                .format(self.printable_name)
            )
            for file in package_files:
                print('  {}'.format(file))
        else:
            print('{}: nothing to upload'.format(self.printable_name))

    def serve(self):
        print('{}: is not served'.format(self.printable_name))


class DirectoryUploadError(UploadError):

    def __init__(self, error, package_file):
        super(DirectoryUploadError, self).__init__(package_file)

        self.error = error

    def __str__(self):
        return (
            'There was an error during upload of {}: {}'
            .format(self.package_name, self.error)
        )


class DirectoryUploader(BaseUploader):

    def __init__(self, repository):
        super(DirectoryUploader, self).__init__(repository)

        repository.ensure_repo_directory()
        self.directory = repository.directory

    def upload(self, package_file):
        try:
            shutil.copy2(package_file, self.directory)
        except IOError as e:
            raise DirectoryUploadError(e, package_file)


PIPCONF_DIRECTORYREPO = '''\
[global]
no-index = true
find-links = {directory}
'''


class DirectoryRepo(Repo):

    ATTRIBUTES = (
        REPO.TYPE,
        REPO.DIRECTORY,
        REPO.VOLATILE,
        REPO.SERVE_INTERFACE,
        REPO.SERVE_PORT,
        REPO.SERVE_USERNAME,
        REPO.SERVE_PASSWORD,
    )

    DEFAULTS = {
        REPO.SERVE_INTERFACE: '0.0.0.0',
        REPO.SERVE_PORT: '8080',
        REPO.VOLATILE: 'no',
    }

    UPLOADER = DirectoryUploader

    def get_as_pip_conf(self):
        return PIPCONF_DIRECTORYREPO.format(directory=self.directory)

    def download_packages(self, package_spec, directory):
        self.ensure_repo_directory()

        msg = ' * Downloading {} and its dependencies'.format(package_spec)
        print(bold(msg))
        pip_install(
            '--no-use-wheel',
            '--find-links', self.directory,
            '--no-index',
            '--download', directory.path,
            package_spec,
        )

    def ensure_repo_directory(self):
        if not os.path.isdir(self.directory):
            os.makedirs(self.directory)

    def serve(self, pypi_server=PyPI):
        self.ensure_repo_directory()

        server = pypi_server()
        server.directory = self.directory
        server.interface = getattr(self, REPO.SERVE_INTERFACE)
        server.port = getattr(self, REPO.SERVE_PORT)
        true = {'y', 'yes', 't', 'true'}
        server.volatile = getattr(self, REPO.VOLATILE).lower() in true

        try:
            username = getattr(self, REPO.SERVE_USERNAME)
            password = getattr(self, REPO.SERVE_PASSWORD)
        except AttributeError:
            pass
        else:
            server.add_user(username, password)

        server.serve()


PYPIRC = '''\
[distutils]
index-servers =
    {0.name}

[{0.name}]
repository: {0.upload_url}
username: {0.username}
password: {0.password}
'''


class TwineUploadError(UploadError):
    pass


class TwineUploader(BaseUploader):

    '''Upload packages with `twine`

    `twine` requires a ~/.pypirc, so HOME is changed to a temporary directory
    that contains a single .pypirc file with content generated for
    the destination repository.
    '''

    TWINE_UPLOAD = os.path.join(
        os.path.dirname(sys.executable),
        'twine-upload'
    )

    def __init__(self, repository):
        super(TwineUploader, self).__init__(repository)

        self.pypirc_dir = tempfile.mkdtemp(
            dir=os.path.expanduser('~'),
            prefix='.pyrene.pypirc'
        )
        pypirc = PYPIRC.format(repository)
        write_file(os.path.join(self.pypirc_dir, '.pypirc'), pypirc)

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.pypirc_dir)
        self.pypirc_dir = None
        self.repository = None

    def upload(self, package_file):
        with set_env('HOME', self.pypirc_dir):
            cmd = [
                self.TWINE_UPLOAD,
                '--repository', self.repository,
                '--comment', 'Uploaded with Pyrene',
                package_file
            ]
            print_command(cmd)
            retcode = subprocess.call(
                cmd,
                stdout=sys.stdout,
                stderr=sys.stderr
            )

        if retcode:
            raise TwineUploadError(package_file)


PIPCONF_HTTPREPO = '''\
[global]
index-url = {download_url}
extra-index-url =
'''


class HttpRepo(Repo):

    ATTRIBUTES = (
        REPO.TYPE,
        REPO.UPLOAD_URL,
        REPO.DOWNLOAD_URL,
        REPO.USERNAME,
        REPO.PASSWORD,
    )

    DEFAULTS = {}

    UPLOADER = TwineUploader

    def get_as_pip_conf(self):
        return PIPCONF_HTTPREPO.format(download_url=self.download_url)

    def download_packages(self, package_spec, directory):
        msg = ' * Downloading {} and its dependencies'.format(package_spec)
        print(bold(msg))
        pip_install(
            '--no-use-wheel',
            '--index-url', self.download_url,
            '--download', directory.path,
            package_spec,
        )

    def serve(self):
        print('Externally served at url {}'.format(self.download_url))
