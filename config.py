import os
from dotenv import load_dotenv
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    ''' Base configurations class '''
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    EMAIL_PATTERN = "^([\w\.\-]+)@([\w\-]+)((\.(\w){2,3})+)$"
    PHONE_PATTERN = "^\+(?:[0-9]){6,14}[0-9]$"

    UPLOAD_FOLDER = "uploads"
    ALLOWED_EXTENSIONS = {'png', 'jpg'}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    JWT_ERROR_MESSAGE_KEY = 'message'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)


class ProductionConfig(Config):
    ''' Extend base config with production config '''
    SECRET_KEY = os.environ['SECRET_KEY']
    # replace url prefix "postgres" with "postgresql" as SQLALCHEMY has dropped support for "postgres" (for heroku)
    # see https://stackoverflow.com/a/64698899/10272966
    # see https://stackoverflow.com/a/66787229/10272966
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL'].replace(
        '://', 'ql://', 1) if os.environ['DATABASE_URL'].startswith('postgres://') else os.environ['DATABASE_URL']


class TestingConfig(Config):
    ''' Extend base config with testing config '''
    TESTING = True
    SECRET_KEY = 'test'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + \
        os.path.join(basedir, 'tests/test.db')
