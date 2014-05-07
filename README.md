<figure>
  <img src="docs/pyrene.png"/>
  <figcaption>Pyrene</figcaption>
</figure>

a _Py_ thon _Re_ pository _Ne_ twork tool
=========================================

I am a tool to help your interactions with Python package repositories.

For example I can copy packages between repos.

I provide a shell-like environment as primary interface - with help and completion for commands and attributes, but I can be used as a command-line tool as well.

There are two types of repos I support:

- http repos, e.g.
    - https://pypi.python.org - the global python public package repo
    - project specific PyPI server - defined by you or your company, for deployment
- directory repos, that is
    - a directory with package files, for fast/offline development
    - `~/.pip/local` - one such directory


Installation
============

From PyPI:

```
mkvirtualenv sys-pyrene
pip install pyrene
```

Directly from GitHub:

`master` branch is always the latest release, so it is safe to install with

```shell
mkvirtualenv sys-pyrene
pip install git+https://github.com/krisztianfekete/pyrene.git
```

As an extra, in order to have `pyrene` without activating its `virtualenv` I do the following:

```shell
ln -s ~/.virtualenvs/sys-pyrene/bin/pyrene ~/bin
```

Usage
=====

My state consists of:
- set of repositories
- an active repository (initially None) that is used for the repo parameter when it is not given for most commands

I support the following commands:

- changing state
  - [un]defining repositories - [http_repo], [directory_repo], [forget]
  - [work_on]
  - changing repository parameters [set], [unset], [setup_for_pip_local], [setup_for_pypi_python_org]
- showing details about the state - [list], [show]
- operations on repos - [copy], [serve], [use]

[http_repo]: docs/commands.md#http_repo
[directory_repo]: docs/commands.md#directory_repo
[forget]: docs/commands.md#forget
[work_on]: docs/commands.md#work_on
[set]: docs/commands.md#set
[unset]: docs/commands.md#unset
[setup_for_pip_local]: docs/commands.md#setup_for_pip_local
[setup_for_pypi_python_org]: docs/commands.md#setup_for_pypi_python_org
[list]: docs/commands.md#list
[show]: docs/commands.md#show
[copy]: docs/commands.md#copy
[serve]: docs/commands.md#serve
[use]: docs/commands.md#use


Development
===========

Fork the [repo](https://github.com/krisztianfekete/pyrene) and create a pull request against the `develop` branch.

The reason is: I am being developed using `git flow` on branch `develop`.
`master` is the release branch.

`Pyrene` is a work in progress, with lots of sharp edges, miswordings, etc.

So

contributions
-------------

- reporting issues
- improving documentation
- improving on the simplicity and clarity of the code/interface
- adding relevant tests
- providing new badly missing features (preferably with tests)
- showing alternatives of me

are welcome.

Guidelines:
-----------

- all code should be extremely simple and clear, including tests
- all features require unit tests
- zero messages from flake8
- usability, simplicity wins over feature completeness
- the smallest the change, the better

The current code might violate these, but it is then considered a bug.
Fixing any of these violations - even if it looks trivial is welcome!

External packages/tools:
------------------------

- packages are downloaded with [pip](http://www.pip-installer.org).
- packages are uploaded with code adopted from [twine](https://pypi.python.org/pypi/twine), unfortunately `twine` is not used directly.
- local packages are served with [pypi-server](https://pypi.python.org/pypi/pypiserver)
