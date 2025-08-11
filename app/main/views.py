from flask import render_template, current_app
from . import main

@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@main.route('/activity', methods=['GET',])
def activity():
    return render_template('activity.html')