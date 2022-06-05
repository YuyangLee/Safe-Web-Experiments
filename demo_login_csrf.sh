#!/bin/bash
rm data.db
export set FLASK_APP=app_login_csrf.py
flask run
