from flask import redirect, render_template, current_app, session, url_for
from . import main
from app.decorators import login_required


@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')