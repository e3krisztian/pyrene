paix - Pa[ckage] I[nde]x [Tool], or peace

I am a tool to manage your interactions with Python package repositories.
I potentially enable you to efficiently use multiple repos.

There are three types of repos you need to know of:
- https://pypi.python.org - the global python public package repo
- ~/.pip/local - a directory with package files, for fast development
- project specific PyPI server - defined by you or your company, for deployment

You need to know, that
- there is only one active index at a time, defined by configuration files `~/.pip/pip.conf` and `~/.pypirc`
- installation of packages is done with [pip](http://www.pip-installer.org)
- upload of packages is done with [twine](https://pypi.python.org/pypi/twine)

I support the following commands:

paix use repo
paix copy package[s] repo:
paix define repo download-url [upload-url username password]
paix drop repo
paix listrepos
