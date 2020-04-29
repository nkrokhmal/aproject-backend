import pysftp
from io import BytesIO


class SftpClient(object):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)
        else:
            self.sftp_client = None
            self.upload_path = None
            self.host = None

    def init_app(self, app):
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        self.host = app.config.get('SFTP_HOST')
        self.sftp_client = pysftp.Connection(
            host=app.config.get('SFTP_HOST'),
            username=app.config.get('SFTP_USERNAME'),
            password=app.config.get('SFTP_PASSWORD'),
            cnopts=cnopts)
        self.upload_path = app.config.get('SFTP_BASE_PATH')

    def create_url(self, path):
        return 'http://{}/{}'.format(self.host, path)

    def upload_file(self, local_path, remote_path):
        self.sftp_client.put(localpath=local_path, remotepath=self.upload_path + remote_path)

    def upload_file_remote(self, local_path, remote_path):
        self.sftp_client.put(localpath=local_path, remotepath=remote_path)

    def upload_file_fo(self, file, remote_path):
        self.sftp_client.putfo(file, remotepath=self.upload_path + remote_path)

    def download_file(self, remote_path):
        file = BytesIO()
        self.sftp_client.getfo(self.upload_path + remote_path, file)
        file.seek(0)
        return file

    def download_file_local(self, local_path, remote_path):
        self.sftp_client.get(self.upload_path + remote_path, localpath=local_path)

