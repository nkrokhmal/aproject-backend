from flask import jsonify
from .. import db
from .. import sftp_client
from ..models import *
from . import api
import werkzeug
from flask_restplus import reqparse
from datetime import datetime
from .errors import bad_request
import scipy.io as sio
import matplotlib.pyplot as plt
import base64
import io
import numpy as np
import json


def show_model(data, dx):
    mat_contents = sio.loadmat(data)
    keys = sorted(mat_contents.keys())
    pressure_field = mat_contents[keys[0]]
    figure = plt.figure(figsize=(5, 5))

    n = pressure_field.shape[0]
    extent = [- n * dx / 2, n * dx / 2, - n * dx / 2, n * dx / 2]
    im = plt.matshow(np.abs(pressure_field), fignum=figure.number, extent=extent)
    plt.colorbar()
    buffer = io.BytesIO()
    figure.savefig(buffer, format='png')
    buffer.seek(0)
    # result_image = base64.b64encode(buffer.getvalue())
    return buffer


def create_parser():
    try:
        parser = reqparse.RequestParser()
        parser.add_argument(
            'ModelFile', type=werkzeug.FileStorage, location='files', required=True)
        parser.add_argument(
            'Dx', type=float, location='form', required=True)
        parser.add_argument(
            'ModelName', type=str, location='form', required=True)
        parser.add_argument(
            'Frequency', type=float, location='form', required=True)
        parser.add_argument(
            'SpeedOfSound', type=float, location='form', required=True)
        parser.add_argument(
            'DensityOfMedium', type=float, location='form', required=True)
        parser.add_argument(
            'ZSurf', type=float, location='form', required=True)

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
        frequency = args['Frequency']
        speed_of_sound = args['SpeedOfSound']
        density_of_medium = args['DensityOfMedium']
        dx = args['Dx']
        z_surf = args['ZSurf']

        params = json.dumps({'dx': dx,
                             'frequency': frequency,
                             'speed_of_sound': speed_of_sound,
                             'density_of_medium': density_of_medium,
                             'z_surf': z_surf})
        model_path = 'models/{}.mat'.format(model_name)
        distribution_path = 'distributions/{}.jpg'.format(model_name)

        model_file_bytes = io.BytesIO(model_file.read())
        figure = show_model(model_file_bytes, dx)
        distribution_file = figure

        model_file_bytes.seek(0)
        sftp_client.upload_file_fo(model_file_bytes, model_path)
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
        except Exception as e:
            return str(e)

        base64_figure = base64.b64encode(figure.getvalue()).decode('ascii')
        return jsonify({'figure': base64_figure}), 201
    except Exception as e:
        return jsonify('Exception occured {}'.format(e))

