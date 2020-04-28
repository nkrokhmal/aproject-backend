from sqlalchemy import Column, DateTime, String, Integer, func, ForeignKey
from . import db


class Permissions:
    USER = 1


class Role(db.Model):
    __tablename__ = 'Roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role')

    def __repr__(self):
        return '<Role %r>' % self.name


class Status(db.Model):
    __tablename__ = 'Statuses'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String)

    def __repr__(self):
        return '<Status %r>' % self.status

    @staticmethod
    def insert_default_status():
        from sqlalchemy.exc import IntegrityError
        status_active = Status(id=1, status='Active')
        status_disabled = Status(id=2, status='Disabled')

        db.session.add(status_active)
        db.session.add(status_disabled)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


class Model(db.Model):
    __tablename__ = 'Models'
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String, unique=True)
    model_path = db.Column(db.String)
    pressure_distribution_path = db.Column(db.String)
    creation_time = db.Column(db.DateTime, default=func.now())
    params = db.Column(db.String)
    status_id = db.Column(db.ForeignKey('Statuses.id'))

    def __repr__(self):
        return '<Status %r>' % self.model_name

    def to_json(self):
        return {
            'id': self.id,
            'model_name': self.model_name,
            'model_path': self.model_path,
            'pressure_distribution_path': self.pressure_distribution_path,
            'creation_time': self.creation_time,
            'params': self.params,
            'status_id': self.status_id
        }


class ModelResult(db.Model):
    __tablename__ = 'ModelResults'
    id = db.Column(db.Integer, primary_key=True)
    x_force = db.Column(db.Float)
    y_force = db.Column(db.Float)
    z_force = db.Column(db.Float)
    force_data_path = db.Column(db.String)
    force_image_path = db.Column(db.String)
    model_params = db.Column(db.String)
    status_id = db.Column(db.ForeignKey('Statuses.id'))
    model_id = db.Column(db.Integer, db.ForeignKey('Models.id'))

    # @staticmethod
    def to_json(self):
        return {
            'id': self.id,
            'x_force': self.x_force,
            'y_force': self.y_force,
            'z_force': self.x_force,
            'force_data_path': self.force_data_path,
            'force_image_path': self.force_image_path,
            'model_params': self.model_params,
            'status_id': self.status_id,
            # 'model': url_for('api.get_model', id=self.model_id, _external=True)
        }


class User(db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    creation_time = db.Column(db.DateTime, default=func.now())
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('Roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username