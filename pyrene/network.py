# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import os
try:
    from ConfigParser import RawConfigParser
except ImportError:
    def RawConfigParser():
        import configparser
        return configparser.ConfigParser(interpolation=None)

from .repos import BadRepo, DirectoryRepo, HttpRepo
from .constants import REPO, REPOTYPE


class UnknownRepoError(NameError):
    '''Repo is not defined at all'''


class Network(object):

    REPO_TYPES = {
        REPOTYPE.DIRECTORY,
        REPOTYPE.HTTP,
    }

    REPO_ATTRIBUTES = set(
        DirectoryRepo.ATTRIBUTES
    ).union(
        set(HttpRepo.ATTRIBUTES)
    )

    REPO_SECTION_PREFIX = 'repo:'

    TYPE_TO_CLASS = {
        REPOTYPE.DIRECTORY: DirectoryRepo,
        REPOTYPE.HTTP: HttpRepo,
    }

    # name of active/default/ repo
    active_repo = None

    def __init__(self, filename):
        self._repo_store_filename = filename
        self._config = None
        self.active_repo = None
        self.reload()

    def reload(self):
        self._config = RawConfigParser()
        if os.path.exists(self._repo_store_filename):
            self._config.read(self._repo_store_filename)

    def _save(self):
        with open(self._repo_store_filename, 'wt') as f:
            self._config.write(f)

    def check_repo_exists(self, repo_name):
        repokey = self.REPO_SECTION_PREFIX + repo_name
        if not self._config.has_section(repokey):
            raise UnknownRepoError(repo_name)

    def get_repo(self, repo_name):
        repo_name = repo_name or self.active_repo
        self.check_repo_exists(repo_name)

        attributes = self.get_attributes(repo_name)
        repo_type = attributes.get(REPO.TYPE)

        repo_class = self.TYPE_TO_CLASS.get(repo_type, BadRepo)
        return repo_class(repo_name, attributes)

    def define(self, repo_name):
        repokey = self.REPO_SECTION_PREFIX + repo_name
        self._config.add_section(repokey)
        self._save()

    def forget(self, repo_name):
        repokey = self.REPO_SECTION_PREFIX + repo_name
        self._config.remove_section(repokey)
        self._save()

    def set(self, repo_name, attribute, value):
        self.check_repo_exists(repo_name)
        repokey = self.REPO_SECTION_PREFIX + repo_name
        self._config.set(repokey, attribute, value)
        self._save()

    def unset(self, repo_name, attribute):
        repokey = self.REPO_SECTION_PREFIX + repo_name
        self._config.remove_option(repokey, attribute)
        self._save()

    @property
    def repo_names(self):
        return [
            section[len(self.REPO_SECTION_PREFIX):]
            for section in self._config.sections()
            if section.startswith(self.REPO_SECTION_PREFIX)
        ]

    def get_attributes(self, repo_name):
        repokey = self.REPO_SECTION_PREFIX + repo_name
        if not self._config.has_section(repokey):
            raise UnknownRepoError(repo_name)

        attributes = {
            attribute: self._config.get(repokey, attribute)
            for attribute in self._config.options(repokey)
        }
        return attributes

    # more complicated operations
    def define_http_repo(self, repo):
        self.define(repo)
        self.set(repo, REPO.TYPE, REPOTYPE.HTTP)

    def define_directory_repo(self, repo):
        self.define(repo)
        self.set(repo, REPO.TYPE, REPOTYPE.DIRECTORY)

    def setup_for_pypi_python_org(self, repo):
        self.set(repo, REPO.TYPE, REPOTYPE.HTTP)
        self.set(repo, REPO.DOWNLOAD_URL, 'https://pypi.python.org/simple/')
        self.set(repo, REPO.UPLOAD_URL, 'https://pypi.python.org/pypi')

    def setup_for_pip_local(self, repo):
        piplocal = os.path.expanduser('~/.pip/local')
        self.set(repo, REPO.TYPE, REPOTYPE.DIRECTORY)
        self.set(repo, REPO.DIRECTORY, piplocal)

    def import_pypirc(self, pypirc_filename):
        pypirc = RawConfigParser()
        pypirc.read(pypirc_filename)

        def copy_attr(repo, key, repoattr):
            if pypirc.has_option(repo, key):
                value = pypirc.get(repo, key)
                self.set(repo, repoattr, value)

        for repo in pypirc.sections():
            if repo != 'distutils':
                self.define(repo)
                self.set(repo, REPO.TYPE, REPOTYPE.HTTP)
                copy_attr(repo, 'repository', REPO.UPLOAD_URL)
                copy_attr(repo, 'username', REPO.USERNAME)
                copy_attr(repo, 'password', REPO.PASSWORD)

    def add_known_repos(self, dot_pypirc):
        self.import_pypirc(dot_pypirc)

        PYPI = 'pypi'
        if PYPI not in self.repo_names:
            self.define_http_repo(PYPI)
            self.setup_for_pypi_python_org(PYPI)

        LOCAL = 'local'
        if LOCAL not in self.repo_names:
            self.define_directory_repo(LOCAL)
            self.setup_for_pip_local(LOCAL)
