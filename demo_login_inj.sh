#!/bin/bash
rm data.db
export set FLASK_APP=app_login_inj.py
flask run
