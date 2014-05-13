# Copyright 2013 Donald Stufft
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Extracted from twine & modified by Krisztian Fekete
# Note: similar code exists in distutils.command.upload

from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals

import hashlib
import os.path

import pkginfo
import pkg_resources
import requests
import re
import httplib


class BDist(pkginfo.BDist):

    @property
    def py_version(self):
        pkgd = pkg_resources.Distribution.from_filename(self.filename)
        return pkgd.py_version


class SDist(pkginfo.SDist):

    py_version = None


def get_whl_py_version(filename):
    wheel_file_re = re.compile(
        r"""
        ^(?P<namever>(?P<name>.+?)(-(?P<ver>\d.+?))?)
        ((-(?P<build>\d.*?))?-(?P<pyver>.+?)-(?P<abi>.+?)-(?P<plat>.+?)
        \.whl|\.dist-info)$
        """,
        re.VERBOSE
    )

    wheel_info = wheel_file_re.match(filename)
    return wheel_info.group("pyver")


class Wheel(pkginfo.Wheel):

    @property
    def py_version(self):
        return get_whl_py_version(os.path.basename(self.filename))


DIST_TYPES = {
    "bdist_wheel": Wheel,
    "bdist_egg": BDist,
    "sdist": SDist,
}

DIST_EXTENSIONS = {
    ".whl": "bdist_wheel",
    ".egg": "bdist_egg",
    ".tar.bz2": "sdist",
    ".tar.gz": "sdist",
    ".zip": "sdist",
}


def get_dtype(filename):
    '''Determine distribution type'''
    for ext, dtype in DIST_EXTENSIONS.items():
        if filename.endswith(ext):
            return dtype

    raise ValueError(
        "Unknown distribution format: '%s'" %
        os.path.basename(filename)
    )


# "unit tests":
assert 'sdist' == get_dtype('pkg.tar.gz')
assert 'sdist' == get_dtype('pkg.zip')
# ? assert 'sdist' == get_dtype('pkg.tgz')
assert 'bdist_egg' == get_dtype('pkg.egg')
assert 'bdist_wheel' == get_dtype('pkg.whl')


def get_meta(filename, dtype):
    return DIST_TYPES[dtype](filename)


def upload(filename, signature, repository, username, password, comment):
    # Extract the metadata from the package
    dtype = get_dtype(filename)
    meta = get_meta(filename, dtype)

    # Fill in the data - send all the meta-data in case we need to
    # register a new release
    data = {
        # action
        ":action": "file_upload",
        "protcol_version": "1",

        # identify release
        "name": meta.name,
        "version": meta.version,

        # file content
        "filetype": dtype,
        "pyversion": meta.py_version,

        # additional meta-data
        "metadata_version": meta.metadata_version,
        "summary": meta.summary,
        "home_page": meta.home_page,
        "author": meta.author,
        "author_email": meta.author_email,
        "maintainer": meta.maintainer,
        "maintainer_email": meta.maintainer_email,
        "license": meta.license,
        "description": meta.description,
        "keywords": meta.keywords,
        "platform": meta.platforms,
        "classifiers": meta.classifiers,
        "download_url": meta.download_url,
        "supported_platform": meta.supported_platforms,
        "comment": comment,

        # PEP 314
        "provides": meta.provides,
        "requires": meta.requires,
        "obsoletes": meta.obsoletes,

        # Metadata 1.2
        "project_urls": meta.project_urls,
        "provides_dist": meta.provides_dist,
        "obsoletes_dist": meta.obsoletes_dist,
        "requires_dist": meta.requires_dist,
        "requires_external": meta.requires_external,
        "requires_python": meta.requires_python,
    }

    pypi_filename = os.path.basename(filename)

    with open(filename, "rb") as fp:
        content = fp.read()
        filedata = {
            "content": (pypi_filename, content),
        }
        if signature:
            filedata["gpg_signature"] = (pypi_filename + ".asc", signature)
        data["md5_digest"] = hashlib.md5(content).hexdigest()

    session = requests.session()
    resp = session.post(
        repository,
        data=dict((k, v) for k, v in data.items() if v),
        files=filedata,
        auth=(username, password),
    )

    if not resp.ok:
        raise UploadError(resp.status_code)


class UploadError(Exception):

    def __init__(self, status_code):
        self.status_code = status_code
        self.status_text = httplib.responses.get(int(status_code))

    def __str__(self):
        return (
            'UploadError - HTTP {}: {}'
            .format(self.status_code, self.status_text)
        )

    __unicode__ = __str__
