import os
import threading

import flask
from flask import render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from fs import fs

import env_variables
from database import users, categories, places
from app import app
from scraping import scraping2gis

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app_root = os.path.dirname(os.path.abspath(__file__))


class User:
    def __init__(self, username):
        self.username = username

    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.username


@login_manager.user_loader
def user_loader(username):
    u = users.find_by_username(username)
    if not u:
        return None
    return User(username=u['name'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users.find_by_username(username)
        if user and user['password'] == password:
            flask_user = User(username=user['name'])
            login_user(flask_user)
            return redirect(request.args.get("next") or url_for('admin'))
        else:
            return render_template('login.html', message="Не удалось войти")
    else:
        return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/admin')
@login_required
def admin():
    cats_iter = categories.get_all({"_id": 0})
    cat = list(cats_iter)
    l = len(cat)
    places_list = places.collect.aggregate([
        {"$lookup": {
            "from": "fs.files",
            "localField": "photos_id",
            "foreignField": "_id",
            "as": "photos",
        }},
        {"$unset": "photos_id"},
        {"$group": {
            "_id": "$category_id",
            "places": {"$push": {
                "name": "$name",
                "photos_id": "$photos_id",
                "description": "$description",
                "photos": "$photos",
                "_id": "$_id"
            }}
        }},
        {"$lookup": {
            "from": "categories",
            "localField": "_id",
            "foreignField": "_id",
            "as": "category",
        }},
        {"$unset": "_id"},
    ])

    return render_template('admin.html', username=current_user.username, categorylength=l, categorylist=cat, places_list=places_list)


@app.route('/add_category', methods=['POST'])
@login_required
def add_category():
    name = request.form['name']
    categories.add(name)
    return redirect(url_for('admin'))


@app.route('/add_place', methods=['POST'])
@login_required
def add_place():
    name = request.form['name']
    description = request.form['description']
    category_name = request.form['category']
    parsing_link = request.form['2gis']
    files = request.files.getlist('photos')
    photos_id = []
    for i in files:
        contents = i.read()
        filename = secure_filename(i.filename)
        id = fs.put(contents, filename=filename)
        photos_id.append(id)

    reviews = None
    latitude = None
    longtitude = None
    rating = None
    ratings_number = None
    url = None
    if parsing_link:
        parsed_data = scraping2gis.get_data(parsing_link)
        reviews = parsed_data["reviews"]
        latitude = parsed_data["latitude"]
        longtitude = parsed_data["longtitude"]
        rating = parsed_data["rating"]
        ratings_number = parsed_data["ratings_number"]
        url = parsed_data["url"]

    places.add(name, photos_id, description, category_name, reviews=reviews, lat=latitude, long=longtitude, rating=rating, ratings_number=ratings_number, url=url)
    return redirect(url_for('admin'))


@app.route('/insert_place', methods=['POST'])
@login_required
def insert_place():
    place_id = request.args.get('id')
    name = request.form['name']
    description = request.form['description']
    parsing_link = request.form['2gis']
    category_name = request.form['category']
    files = request.files.getlist('photos')
    photos_id = []
    for i in files:
        contents = i.read()
        filename = secure_filename(i.filename)
        if f := fs.find_one({'filename': filename}):
            fs.delete(f._id)
        id = fs.put(contents, filename=filename)
        photos_id.append(id)

    reviews = None
    latitude = None
    longtitude = None
    rating = None
    ratings_number = None
    url = None
    if parsing_link:
        parsed_data = scraping2gis.get_data(parsing_link)
        reviews = parsed_data["reviews"]
        latitude = parsed_data["latitude"]
        longtitude = parsed_data["longtitude"]
        rating = parsed_data["rating"]
        ratings_number = parsed_data["ratings_number"]
        url = parsed_data["url"]

    places.update(place_id, name, photos_id, description, category_name, reviews=reviews, lat=latitude, long=longtitude, rating=rating, ratings_number=ratings_number, url=url)
    return redirect(url_for('admin'))


@app.route('/delete_category', methods=['GET'])
@login_required
def delete_category():
    name = request.args.get("name")
    categories.delete_by_name(name)
    return redirect(url_for('admin'))


@app.route('/delete_place', methods=['GET'])
@login_required
def delete_place():
    id = request.args.get("id")
    places.delete_by_id(id)
    return redirect(url_for('admin'))


@app.route('/update_place', methods=['GET'])
@login_required
def update_place():
    id = request.args.get("id")
    place = places.get_by_id(id)
    category_list = categories.get_all()
    return render_template('update_place.html', place=place, category_list=list(category_list))


@app.route('/api/get-file/<name>')
def get_file(name=None):
    f = fs.get_last_version(name)
    r = app.response_class(f, direct_passthrough=True, mimetype='application/octet-stream')
    r.headers.set('Content-Disposition', 'attachment', filename=name)
    return r
