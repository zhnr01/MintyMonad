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
    
class NFT(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token_id = db.Column(db.Integer, nullable=False)
    contract_address = db.Column(db.String(42), nullable=False)
    name = db.Column(db.String(100))
    image_url = db.Column(db.String(255))
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    offers = db.relationship('Offer', backref='nft', lazy=True)

    def __repr__(self):
        return f'<NFT {self.name} #{self.token_id}>'

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nft_id = db.Column(db.Integer, db.ForeignKey('nft.id'), nullable=False)  # Note lowercase 'nft'
    buyer_wallet = db.Column(db.String(42), nullable=False)
    offer_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='pending')

    def __repr__(self):
        return f'<Offer for NFT {self.nft_id} at {self.offer_price}>'