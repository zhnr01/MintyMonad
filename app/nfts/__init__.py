from flask import Blueprint

nfts = Blueprint('nfts', __name__)

from . import views  
