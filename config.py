import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'localhost'
    MAIL_PORT = os.environ.get('MAIL_PORT') or 1025
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'mail'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'password'
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or False
    APROJECT_MAIL_SENDER = os.environ.get('APROJECT_MAIL_SENDER') or 'krokhmal11@gmail.com'
    APROJECT_ADMIN = os.environ.get('APROJECT_ADMIN') or 'krokhmal11@gmail.com'
    CIRCULATE_MAIL_SUBJECT_PREFIX = '[Aproject]'

    @staticmethod
    def init_app(app):
        pass


class DebugConfig(Config):
    SQL_CONNECTION_STRING = os.environ.get('SQLALCHEMY_DATABASE_URI')
    SFTP_HOST = os.environ.get('SFTP_HOST')
    SFTP_USER = os.environ.get('SFTP_USERNAME')
    SFTP_PASSWORD = os.environ.get('SFTP_PASSWORD')
    SFTP_BASE_PATH = os.environ.get('SFTP_BASE_PATH')


class ProductionConfig(Config):
    SSL_DISABLE = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    SFTP_HOST = os.environ.get('SFTP_HOST')
    SFTP_USERNAME = os.environ.get('SFTP_USERNAME')
    SFTP_PASSWORD = os.environ.get('SFTP_PASSWORD')
    SFTP_BASE_PATH = os.environ.get('SFTP_BASE_PATH')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        import logging
        from logging.handlers import SMTPHandler
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
                fromaddr=cls.APROJECT_MAIL_SENDER,
                toaddrs=cls.APROJECT_ADMIN,
                subject=cls.CIRCULATE_MAIL_SUBJECT_PREFIX + ' Application Error',
                credentials=credentials,
                secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

config = {
    'debug': DebugConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}