import os
from env_variables import secret_key, url
from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
