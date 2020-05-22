import base64
import io
import os

from flask import jsonify

from .. import db
from .. import sftp_client
from ..models import *
from . import api
import json
from flask_restplus import reqparse
from ..utils.rfc_client import Object, Wave, Coordinates, Spectrum, Points
import time
import numpy as np
from .errors import bad_request


def create_parser():
    parser = reqparse.RequestParser()
    parser.add_argument('Radius', type=float, location='form', required=False)
    parser.add_argument('LongitudinalSpeed', type=float, location='form', required=False)
    parser.add_argument('TransverseSpeed', type=float, location='form', required=False)
    parser.add_argument('DensityOfScatterer', type=float, location='form', required=False)
    parser.add_argument('Frequency', type=float, location='form', required=False)
    parser.add_argument('SpeedOfSound', type=float, location='form', required=False)
    parser.add_argument('DensityOfMedium', type=float, location='form', required=False)
    parser.add_argument('Dx', type=float, location='form', required=False)
    parser.add_argument('Type', type=str, location='form', required=False)
    parser.add_argument('From', type=float, location='form', required=False)
    parser.add_argument('To', type=float, location='form', required=False)
    parser.add_argument('Step', type=float, location='form', required=False)
    parser.add_argument('ModelPath', type=str, location='form', required=False)
    parser.add_argument('ModelName', type=str, location='form', required=False)
    parser.add_argument('ZSurf', type=float, location='form', required=False)
    return parser


@api.route('/scatterer', methods=['POST'])
def post_scatterer():
    try:
        parser = create_parser()
        args = parser.parse_args()
        model_path = args['ModelPath']
        model_id = args['ModelName']

        cur_time = time.strftime('%Y%m%d%H%M%S')
        force_dict_name = '{}_{}.txt'.format(model_id, cur_time)
        force_image_name = '{}_{}.png'.format(model_id, cur_time)
        force_dict_path = '/opt/download/{}'.format(force_dict_name)
        force_image_path = '/opt/download/{}'.format(force_image_name)
        model_local_path = '/opt/download/{}.mat'.format(model_id)
        force_numpy_path = '/opt/download/{}_{}.txt'.format(model_id, cur_time)

        obj = Object(a=args['Radius'], rho=args['DensityOfScatterer'], c_l=args['LongitudinalSpeed'],
                     c_t=args['TransverseSpeed'])
        wave = Wave(f=args['Frequency'], c=args['SpeedOfSound'], rho=args['DensityOfMedium'])
        spectrum = Spectrum(dx=args['Dx'])

        if args['Type'] == 'X':
            coordinates = Coordinates(x=np.arange(args['From'], args['To'], args['Step']), y=np.array([0.0]),
                                      z=np.array([0.0]), z_surf=args['ZSurf'])
            type_coordinate = 0
        elif args['Type'] == 'Y':
            coordinates = Coordinates(x=np.array([0.0]), y=np.arange(args['From'], args['To'], args['Step']),
                                      z=np.array([0.0]), z_surf=args['ZSurf'])
            type_coordinate = 1
        else:
            coordinates = Coordinates(x=np.array([0.0]), y=np.array([0.0]),
                                      z=np.arange(args['From'], args['To'], args['Step']), z_surf=args['ZSurf'])
            type_coordinate = 2

        sftp_client.download_file_local(model_local_path, model_path)

        points = Points(coordinates, obj, wave, spectrum, model_local_path)
        force, x_force, y_force, z_force, p_scat = points.calculate_force()
        fig = points.build_rad_force(force, type_coordinate)

        fig.savefig(force_image_path)
        np.savetxt(force_numpy_path, force)

        buffer = io.BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        result_image = base64.b64encode(buffer.getvalue())

        sftp_client.upload_file(force_dict_path, 'force/{}'.format(force_dict_name))
        sftp_client.upload_file(force_image_path, 'force_image/{}'.format(force_image_name))

        scatterer_params = dict(args.items())
        del scatterer_params['ModelPath']
        del scatterer_params['ModelName']

        scatterer = ModelResult(
            x_force=x_force,
            y_force=y_force,
            z_force=z_force,
            force_data_path=sftp_client.create_url('force/{}'.format(force_dict_name)),
            force_image_path=sftp_client.create_url('force_image/{}'.format(force_image_name)),
            model_id=model_id,
            model_params=json.dumps(scatterer_params),
            status_id=1
        )

        db.session.add(scatterer)
        try:
            db.session.commit()
        except Exception as e:
            return str(e)

        os.remove(model_local_path)
        os.remove(force_image_path)
        os.remove(force_dict_path)
        return jsonify({'figure': result_image.decode('ascii')}), 201
    except Exception as e:
        return bad_request(e)
