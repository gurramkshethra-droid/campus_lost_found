from datetime import datetime
from flask_login import UserMixin

from extensions import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    items = db.relationship('Item', backref='owner', lazy=True)
    notifications = db.relationship('Notification', backref='recipient', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.email}>'


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    color = db.Column(db.String(60), nullable=True)
    brand = db.Column(db.String(80), nullable=True)
    image = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    lost_matches = db.relationship('Match', backref='lost_item', lazy=True, foreign_keys='Match.lost_item_id')
    found_matches = db.relationship('Match', backref='found_item', lazy=True, foreign_keys='Match.found_item_id')
    claims = db.relationship('Claim', backref='item', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Item {self.title} {self.type}>'


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lost_item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    found_item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    match_score = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Match {self.lost_item_id}-{self.found_item_id} score={self.match_score}>'


class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    location = db.Column(db.String(100))
    color = db.Column(db.String(50))
    brand = db.Column(db.String(50))
    message = db.Column(db.Text)

    status = db.Column(db.String(20), default='pending')
    user = db.relationship('User', backref='claims')


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)