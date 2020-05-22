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
import os
import scipy


def build_focused_beam(r_in=0.0, r_out=0.05, dx=0.001, R0=0.07, f=1e6, rho=1e3, c=1500, Ampl=1):
    Nx = int(2 * np.round(r_out / dx))
    if (-1) ** Nx > 0:
        x_array = np.concatenate([np.arange(Nx / 2 + 1.), np.arange(- Nx / 2 + 1., 0.)])
    elif (-1) ** self.spectrum.Nx < 0:
        x_array = np.concatenate([np.arange((Nx + 1.) / 2), np.arange(- (Nx - 1.) / 2, 0.)])
    x_array = x_array[:, np.newaxis]
    x_array = dx * x_array.astype(float)
    y_array = x_array.copy()
    y_array = y_array.T
    r_array = np.sqrt(x_array ** 2 + y_array ** 2)
    r_array[0, 0] = 1e-12

    K_r1 = 0.5 * (np.sign(r_array - r_in + 1.124e-10) + 1);
    K_r2 = 0.5 * (np.sign(r_out - r_array + 1.123e-10) + 1);
    K_12 = K_r1 * K_r2;
    h_surf = (R0 - ((K_r2 * (R0 ** 2 - r_array ** 2)) ** (1 / 2))) * K_r2;
    Pressure = K_12 * Ampl

    N2 = int(np.round(Nx))

    if (-1) ** N2 > 0:
        x_surf = np.concatenate([np.arange(- N2 / 2 + 1., N2 / 2 + 1.)])
    elif (-1) ** N2 < 0:
        x_surf = np.concatenate([np.arange(- (N2 - 1.) / 2, (N2 + 1.) / 2)])
    x_surf = x_surf[:, np.newaxis]
    x_surf = dx * x_surf.astype(float)
    y_surf = x_surf.copy()
    y_surf = y_surf.T
    z_surf = R0 * 0.9
    p_flat = np.zeros((2 * int(N2), 2 * int(N2))) * (0. + 1j * 0.)
    n_z = np.sqrt(K_12 * (1 - (x_array ** 2 + y_array ** 2) / R0 ** 2))

    def Rayleigh(x_ar, y_ar, z_ar, norm, Pr, f, c, dx, x0, y0, z0):
        r = np.sqrt((x0 - x_ar) ** 2 + (y0 - y_ar) ** 2 + (z0 - z_ar) ** 2)
        p_comp = -1j * f / c * Pr * dx ** 2 / (norm + 1e-13) * np.exp(1j * 2 * np.pi * f / c * r) / r
        p_nm = np.sum(np.sum(p_comp))
        return p_nm

    x_surf_test = dx * np.arange(- N2 / 2 + 1., N2 / 2 + 1.)
    x_surf_test = np.array([x_surf_test] * len(x_surf_test))
    y_surf_test = x_surf_test.T
    z_surf_test = x_surf_test * 0 + R0 * 0.9

    shape = x_surf_test.shape
    x_test = np.asarray(x_surf_test).reshape(-1)
    y_test = np.asarray(y_surf_test).reshape(-1)
    z_test = np.asarray(z_surf_test).reshape(-1)

    result = [Rayleigh(x_array, y_array, h_surf, n_z, Pressure, f, c, dx, x, y, z)
              for x, y, z in zip(x_test, y_test, z_test)]
    p_trans = np.reshape(result, shape)

    p_flat = np.zeros((int(2 * N2), int(2 * N2)))
    p_flat[int(N2 / 2):int(3 * N2 / 2), int(N2 / 2):int(3 * N2 / 2)] = p_trans
    figure1 = plt.figure(figsize=(5, 5))
    m_z = p_flat.shape[0]
    m_x = p_flat.shape[1]
    extent = [- N2 * dx, N2 * dx, - N2 * dx, N2 * dx]
    im1 = plt.matshow(np.abs(p_flat), fignum=figure1.number, extent=extent, aspect='auto')
    plt.colorbar()

    return figure1, p_flat, z_surf


def create_parser():
    parser = reqparse.RequestParser()
    parser.add_argument('RadiusOfHole', type=float, location='form', required=False)
    parser.add_argument('RadiusOfTransducer', type=float, location='form', required=False)
    parser.add_argument('SpatialStep', type=float, location='form', required=False)
    parser.add_argument('CurvativeRadius', type=float, location='form', required=False)
    parser.add_argument('Frequency', type=float, location='form', required=False)
    parser.add_argument('DensityOfWater', type=float, location='form', required=False)
    parser.add_argument('SpeedSoundInWater', type=float, location='form', required=False)
    parser.add_argument('PressureAmplitude', type=float, location='form', required=False)
    parser.add_argument('ModelName', type=str, location='form', required=False)
    return parser


@api.route('/createmodel', methods=['GET', 'POST'])
def create_model():
    parser = create_parser()
    args = parser.parse_args()
    radius_of_hole = args['RadiusOfHole']
    radius_of_transducer = args['RadiusOfTransducer']
    spatial_step = args['SpatialStep']
    curvative_radius = args['CurvativeRadius']
    frequency = args['Frequency']
    density_of_water = args['DensityOfWater']
    speed_of_sound_in_water = args['SpeedSoundInWater']
    pressure_amplitude = args['PressureAmplitude']
    model_name = args['ModelName']

    model_path = 'models/{}.mat'.format(model_name)
    distribution_path = 'distributions/{}.png'.format(model_name)
    model_local_path = '/opt/download/{}.mat'.format(model_name)
    distribution_local_path = '/opt/download/{}.png'.format(model_name)

    figure, p_flat, z_surf = build_focused_beam(r_in=radius_of_hole,
                                                r_out=radius_of_transducer,
                                                dx=spatial_step,
                                                R0=curvative_radius,
                                                f=frequency,
                                                rho=density_of_water,
                                                c=speed_of_sound_in_water,
                                                Ampl=pressure_amplitude)

    figure.savefig(distribution_local_path)
    scipy.io.savemat(model_local_path, {'P_ax': p_flat})

    sftp_client.upload_file(distribution_local_path, distribution_path)
    sftp_client.upload_file(model_local_path, model_path)

    params = {
        "dx": spatial_step,
        "frequency": frequency,
        "speed_of_sound": speed_of_sound_in_water,
        "density_of_medium": density_of_water,
        "z_surf": z_surf
    }
    model = Model(
        model_name=model_name,
        model_path=sftp_client.create_url(model_path),
        pressure_distribution_path=sftp_client.create_url(distribution_path),
        creation_time=datetime.utcnow(),
        params=json.dumps(params),
        status_id=1
    )
    db.session.add(model)
    db.session.commit()

    os.remove(model_local_path)
    os.remove(distribution_local_path)

    buffer = io.BytesIO()
    figure.savefig(buffer, format='png')
    buffer.seek(0)
    base64_figure = base64.b64encode(buffer.getvalue()).decode('ascii')

    return jsonify({'figure': base64_figure}), 201