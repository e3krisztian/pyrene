class REPO:
    '''Repo attributes'''
    TYPE = 'type'

    DIRECTORY = 'directory'
    VOLATILE = 'volatile'
    SERVE_INTERFACE = 'interface'
    SERVE_PORT = 'port'
    SERVE_USERNAME = 'username'
    SERVE_PASSWORD = 'password'

    # This is intentionally the same as SERVE_USERNAME and SERVE_PASSWORD
    # so that new users can get .pyrene configs with valid passwords
    USERNAME = SERVE_USERNAME
    PASSWORD = SERVE_PASSWORD
    DOWNLOAD_URL = 'download_url'
    UPLOAD_URL = 'upload_url'


class REPOTYPE:
    '''Values for REPO.TYPE'''
    DIRECTORY = 'directory'
    HTTP = 'http'


MAX_HISTORY_SIZE = 100
