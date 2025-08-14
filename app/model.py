from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(42), unique=True, nullable=False) 
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    nfts = db.relationship('NFT', backref='owner', lazy=True)

    def __repr__(self):
        return f'<User {self.wallet_address}>'
