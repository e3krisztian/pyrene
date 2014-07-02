.. this is a reST document, intentionally mistyped as .md for viewing on github

.. image::
  https://raw.githubusercontent.com/krisztianfekete/pyrene/master/docs/pyrene.png


A PY-thon RE-pository NE-twork tool
===================================

Python package `repositories` are nodes in a network.

`Pyrene` is a tool to transfer `packages` between repositories

- with an easy syntax:
  sources and targets are both defined as `repo:package`
- with package dependencies, thus the target will be self contained!

`Pyrene` is also an opinionated (read: simple, useful)
configuration tool for `pip`.


Installation
============

As an application into a separate `virtualenv` using `virtualenvwrapper`::

    mkvirtualenv app-pyrene
    pip install pyrene

creating this link is optional, but let's us use `pyrene` outside its virtualenv::

    ln -s ~/.virtualenvs/app-pyrene/bin/pyrene ~/bin


A simple network
================

The following simple network is intended to be a working reference setup for Pyrene.

Repositories are `pypi`, `local`, `private` as defined below:


repo `pypi`
-----------

is a pre-defined repo pointing to the public Python package repository at https://pypi.python.org/simple

It is used for publishing packages of public interest.

It is a *volatile repo*: **project owners can DELETE published packages or even entire projects.**

The obvious package names are mostly already taken.


repo `local`
------------

is a pre-defined repo pointing to the local directory: `~/.pip/local`

The user wants this to be the default repository for new package installs::

    $ pyrene use local

This directory holds all packages needed for development, thus development
can continue offline as well.

The developer has full control over the repository.


repo `private`
--------------

is accessible through a potentially restricted url
`https://packages.proprietary.com/simple`

This repository holds all packages needed for deployments: both publicly
available packages from pypi and in-house developed closed source ones.

The project/company has full control over the repo content.

It is not pre-defined, so define it::

    $ pyrene
    ...
    Pyrene: http_repo private
    Pyrene[private]: set download_url=https://packages.proprietary.com/simple/
    Pyrene[private]: set upload_url=https://packages.proprietary.com/pypi
    Pyrene[private]: set username=<me@company repo>
    Pyrene[private]: set password=<secret>

Here `pyrene` is used in shell mode, and `Pyrene[...]:` is a prompt for
commands.


Usage scenarios
===============

Import a public package for offline use
---------------------------------------

::

    $ pyrene copy pypi:public-package local:

This also copies all the dependencies of `public-package` as well.


Publish an in-house package
---------------------------

::

    $ cd in-house-pkg
    $ python setup.py sdist
    $ pyrene copy dist/in-house-pkg-1.0.0.tgz local:
    $ pyrene copy local:in-house-pkg private:


Deploy an application
---------------------

::

    # make pip use the `private` repository by default by [over]writing `~/.pip/pip.conf`
    $ pyrene use private
    $ mkvirtualenv app
    $ pip install application
    $ start-application
    ...
    # restore the dev-env
    $ deactivate
    $ rmvirtualenv app
    $ pyrene use local


Feedback
========

This is an early release so if you have any problems
(*including usability*), please tell them about at

https://github.com/krisztianfekete/pyrene/issues


Features
========

- shell with help, command completion and colors for configuration and interactive
  operations::

      $ pyrene
      ...
      Pyrene: directory_repo local
      Pyrene[local]: set directory=/path/to/repo
      Pyrene[local]: copy pypi:someinterestingpkg==0.1 local:
      Pyrene[local]: work_on private
      Pyrene[private]: copy local:someinterestingpkg private:
      Pyrene[private]: help use
      ...

- copy packages between repos (and directories)::

      $ pyrene copy source-repo:package-with-lots-of-dependencies destination-repo:

- serve local directory repos over http (package sharing with coworkers?)::

      $ pyrene serve dir-repo

- configure pip (by writing a `~/.pip/pip.conf` file) to use a repo without
  `--index-url` or `--find-links` command line options::

      $ pyrene use repo


Internals
=========

The network configuration is persisted in the file `~/.pyrene`
(including passwords in plain text),
which can be thought of as a combined `~/.pypirc` and `~/.pip/pip.conf`.

All operations are delegated to external tools (not to reinvent the `eggs`):

- downloading packages is delegated to `pip`
- uploading via http/https is delegated to `twine`
- serving a directory is delegated to `pypiserver`

Tools are heavily influenced to work in a certain way by

- giving them approriate command line options
- setting an environment variable
- writing a config file for them

all of them painful manually.

Repositories defined in `~/.pypirc` are imported on first startup, and
the `use` command replaces `~/.pip/pip.conf` to make `pip` work without
options.


Changelog
=========

0.2.0 (2014-07-02)

- wheels are not downloaded anymore - local wheels can still be uploaded
- delegate http uploads to `twine` - simplifies code & license
- status command: show python packaging configuration status
- use command: makes backup of existing config before writing ~/.pip/pip.conf
- add known repos on first run:
   - repositories from `.pypirc` (only sets `upload-url`)
   - `pypi` as `http://pypi.python.org`
   - `local` as `~/.pip/local`
- new command: import_pypirc
- readline history
- show version on startup

0.1.3 (2014-05-13)

- fix #1: existing package at remote http repo stops copy

0.1.2 (2014-05-09)

- setup.cfg: fix keywords & classifiers, early release notice

0.1.1 (2014-05-08)

- initial release - for testing
