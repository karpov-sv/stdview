from flask import Flask

app = Flask(__name__)

app.config['stdview'] = {} # Our own sub-dictionary inside config
stdconf = app.config['stdview'] # Handy shortcut for accessing it

from . import views
