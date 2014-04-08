# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import os
from ConfigParser import RawConfigParser
from .repos import FileRepo, PipLocalRepo, HttpRepo, PyPIRepo

REPOTYPE_FILE = 'file'
REPOTYPE_HTTP = 'http'
REPOTYPE_PYPI = 'pypi'
REPOTYPE_PIPLOCAL = 'piplocal'


class UnknownRepoError(NameError):
    '''Repo is not defined at all'''


class UndefinedRepoType(ValueError):
    '''type was not defined for repo'''


class UnknownRepoType(ValueError):
    '''type was given, but it is unknown'''


KEY_TYPE = 'type'
KEY_DIRECTORY = 'directory'
KEY_USERNAME = 'username'
KEY_PASSWORD = 'password'
KEY_DOWNLOAD_URL = 'download_url'
KEY_UPLOAD_URL = 'upload_url'

TYPE_TO_CLASS = {
    REPOTYPE_FILE: FileRepo,
    REPOTYPE_PIPLOCAL: PipLocalRepo,
    REPOTYPE_HTTP: HttpRepo,
    REPOTYPE_PYPI: PyPIRepo
}


class RepoManager(object):

    REPO_TYPES = {
        REPOTYPE_FILE,
        REPOTYPE_PIPLOCAL,
        REPOTYPE_HTTP,
        REPOTYPE_PYPI,
    }

    REPO_ATTRIBUTES = {
        KEY_TYPE,
        KEY_DIRECTORY,
        KEY_DOWNLOAD_URL,
        KEY_UPLOAD_URL,
        KEY_USERNAME,
        KEY_PASSWORD,
    }

    def __init__(self, filename):
        self._repo_store_filename = filename
        self._config = RawConfigParser()
        if os.path.exists(self._repo_store_filename):
            self._config.read(self._repo_store_filename)

    def _save(self):
        with open(self._repo_store_filename, 'wt') as f:
            self._config.write(f)

    def get_repo(self, repo_name):
        if not self._config.has_option(repo_name, KEY_TYPE):
            if self._config.has_section(repo_name):
                raise UndefinedRepoType(repo_name)
            raise UnknownRepoError(repo_name)

        attributes = self.get_attributes(repo_name)
        repo_type = attributes[KEY_TYPE]

        try:
            return TYPE_TO_CLASS[repo_type](attributes)
        except KeyError:
            raise UnknownRepoType(repo_type)

    def define(self, repo_name):
        self._config.add_section(repo_name)
        self._save()

    def forget(self, repo_name):
        self._config.remove_section(repo_name)
        self._save()

    def set(self, repo_name, key, value):
        self._config.set(repo_name, key, value)
        self._save()

    @property
    def repo_names(self):
        return self._config.sections()

    def get_attributes(self, repo_name):
        attributes = {
            option: self._config.get(repo_name, option)
            for option in self._config.options(repo_name)
        }
        return attributes
