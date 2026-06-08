import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy()

class Card(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    sender_id = db.Column(db.BigInteger, nullable=False)
    template_id = db.Column(db.Integer, nullable=True)
    media_path = db.Column(db.String(255), nullable=True)
    media_type = db.Column(db.String(10), nullable=True) # 'photo' or 'video'
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    sender_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_viewed = db.Column(db.Boolean, default=False)
    reply_text = db.Column(db.Text, nullable=True)

    def __init__(self, **kwargs):
        super(Card, self).__init__(**kwargs)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(days=7)
