from flask import Blueprint

api = Blueprint('api', __name__)

from . import savemodel, modelresult, model, scatterer
