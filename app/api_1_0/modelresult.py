from flask import jsonify, request
from sqlalchemy import or_
from ..utils.utils import AlchemyEncoder
from ..models import *
from .errors import bad_request
from . import api
import json


@api.route('/modelresult', methods=['GET'])
def get_modelresult():
    try:
        model_ids = request.args.getlist("model_id")
        result = db.session.query(ModelResult, Model)\
            .join(Model)\
            .filter(or_(ModelResult.model_id.in_(model_ids), len(model_ids) == 0))\
            .filter(ModelResult.status_id == 1)\
            .filter(Model.status_id == 1)\
            .all()
        return jsonify([json.dumps(x, cls=AlchemyEncoder) for x in result])
    except Exception as e:
        return bad_request(e)


@api.route('/modelresult', methods=['DELETE'])
def delete_modelresult():
    try:
        model_result_id = request.args.get("model_result_id")
        model_result_update = db.session.query(ModelResult)\
            .filter(ModelResult.id == model_result_id)\
            .first()
        print(model_result_update)
        model_result_update.status_id = 2
        db.session.commit()
        return jsonify(model_result_update.to_json())
    except Exception as e:
        return bad_request(e)