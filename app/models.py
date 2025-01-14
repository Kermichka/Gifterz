from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)

    _password = db.Column("password", db.String(512), nullable=False)

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, plain_text_password):
        self._password = generate_password_hash(plain_text_password)

    def check_password(self, plain_text_password):
        return check_password_hash(self._password, plain_text_password)

    @property
    def is_active(self):
        return True


class List(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)


class Present(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey("list.id"), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"))


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    present_id = db.Column(db.Integer, db.ForeignKey("present.id"), nullable=False)
    group_size = db.Column(db.Integer, nullable=False)


class Buyer(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), primary_key=True)
    contribution_amount = db.Column(db.Float, nullable=False)


class Connection(db.Model):
    user_id_1 = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    user_id_2 = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    connection_type = db.Column(db.String(50), nullable=False)
