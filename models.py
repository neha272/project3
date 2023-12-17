from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    key = db.Column(db.String(50), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    msg = db.Column(db.String(280), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    key = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='posts')
    reply_to = db.Column(db.Integer, db.ForeignKey('post.id'))
    replies = db.relationship('Post', backref=db.backref('parent', remote_side=[id]))
