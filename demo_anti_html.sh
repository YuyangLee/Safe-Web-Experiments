#!/bin/bash
rm test.db
export set FLASK_APP=app_anti_html.py
flask run
