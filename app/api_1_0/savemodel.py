from flask import jsonify
from .. import db
from .. import sftp_client
from ..models import *
from . import api
import werkzeug
from flask_restplus import reqparse
from datetime import datetime
from .errors import bad_request


def create_parser():
    try:
        parser = reqparse.RequestParser()
        parser.add_argument(
            'ModelFile', type=werkzeug.FileStorage, location='files', required=True)
        parser.add_argument(
            'DistributionFile', type=werkzeug.FileStorage, location='files', required=True)
        parser.add_argument(
            'ModelName', type=str, location='form', required=True)
        parser.add_argument(
            'Parameters', type=str, location='form', required=True)
        return parser
    except Exception as e:
        return bad_request(e)


@api.route('/savemodel', methods=["POST"])
def post_savemodel():
    try:
        parser = create_parser()
        args = parser.parse_args()
        model_file = args['ModelFile']
        model_name = args['ModelName']
        params = args['Parameters']

        distribution_file = args['DistributionFile']

        model_path = 'models/{}.mat'.format(model_name)
        distribution_path = 'distributions/{}.jpg'.format(model_name)

        sftp_client.upload_file_fo(model_file, model_path)
        sftp_client.upload_file_fo(distribution_file, distribution_path)

        model = Model(
            model_name=model_name,
            model_path=sftp_client.create_url(model_path),
            pressure_distribution_path=sftp_client.create_url(distribution_path),
            creation_time=datetime.utcnow(),
            params=params,
            status_id=1
        )
        db.session.add(model)
        try:
            db.session.commit()
            return jsonify(model.to_json()), 201
        except Exception as e:
            return str(e)
    except Exception as e:
        return bad_request(e)

