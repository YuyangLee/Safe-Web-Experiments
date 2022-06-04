#!/bin/bash
rm test.db
export set FLASK_APP=app_anti_flask.py
flask run
