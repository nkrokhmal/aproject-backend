from flask import jsonify, request, current_app, url_for
from sqlalchemy import or_, and_
from . import api
from .errors import bad_request, ok
from ..models import Model, ModelResult
from .. import db


@api.route('/models', methods=['GET'])
def get_models():
    try:
        model_ids = request.args.getlist("model_id")
        models = db.session.query(Model)\
            .filter(or_(Model.id.in_(model_ids), len(model_ids) == 0))\
            .filter(Model.status_id == 1)\
            .all()
        return jsonify([x.to_json() for x in models])
    except Exception as e:
        return bad_request(e)


@api.route('/models', methods=['DELETE'])
def delete_models():
    try:
        model_ids = request.args.getlist('model_id')
        db.session.query(ModelResult)\
            .filter(and_(ModelResult.model_id.in_(model_ids), len(model_ids) != 0))\
            .filter(ModelResult.status_id == 1)\
            .update({ModelResult.status_id: 2}, synchronize_session=False)
        db.session.query(Model)\
            .filter(and_(Model.id.in_(model_ids), len(model_ids) != 0))\
            .filter(Model.status_id == 1)\
            .update({Model.status_id: 2}, synchronize_session=False)
        db.session.commit()
        return ok("Successfully removed models with id {}".format(model_ids))
    except Exception as e:
        return bad_request(e)
