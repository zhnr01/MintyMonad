from flask import jsonify, render_template
from . import main
from app import db


@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@main.route('/healthz', methods=['GET'])
def healthz():
    return jsonify({'status': 'ok'})


@main.route('/readyz', methods=['GET'])
def readyz():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'ready', 'database': 'ok'})
    except Exception:
        return jsonify({'status': 'not_ready', 'database': 'unavailable'}), 503