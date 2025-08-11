from flask import render_template, current_app
from . import nfts  

@nfts.route('/', methods=['GET'])
def marketplace():
    return render_template('marketplace.html')

@nfts.route('/mine', methods=['GET'])
def my_nfts():
    return render_template('my-nfts.html')

@nfts.route('/mint', methods=['GET'])
def mint():
    return render_template('mint.html')
