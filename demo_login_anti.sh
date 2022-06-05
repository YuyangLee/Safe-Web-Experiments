#!/bin/bash
###
 # @LastEditors: Aiden Li (i@aidenli.net)
 # @Description: Your description
 # @Date: 2022-06-05 13:28:18
 # @LastEditTime: 2022-06-05 14:56:09
 # @Author: Aiden Li
### 
rm data.db
export set FLASK_APP=app_login_anti.py
flask run
