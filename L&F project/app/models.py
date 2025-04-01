from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    phone = db.Column(db.String(20))
    items_lost = db.relationship('Item', backref='owner', lazy=True, 
                               foreign_keys='Item.user_id')
    items_found = db.relationship('Item', backref='finder', lazy=True, 
                                foreign_keys='Item.finder_id')
    claims = db.relationship('Claim', backref='claimer', lazy=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_id = db.Column(db.String(10), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(50))
    status = db.Column(db.String(20), nullable=False)  # 'lost' or 'found'
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_lost_found = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    image_file = db.Column(db.String(20), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    finder_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_claimed = db.Column(db.Boolean, default=False)
    is_resolved = db.Column(db.Boolean, default=False)
    claims = db.relationship('Claim', backref='item', lazy=True)

class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    proof = db.Column(db.Text, nullable=False)
    date_claimed = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    admin_notes = db.Column(db.Text)
    collection_location = db.Column(db.String(100))

class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(20), nullable=False)  # 'verification' or 'reset'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) 