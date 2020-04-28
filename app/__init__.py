from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
from .utils.sftp_client import SftpClient

db = SQLAlchemy()
sftp_client = SftpClient()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    sftp_client.init_app(app)

    from .api_1_0 import api as api_1_0
    app.register_blueprint(api_1_0, url_prefix='/api')

    return app