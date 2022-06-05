import os
from flask import Flask, make_response, redirect, render_template, request, escape
import sqlite3
import hashlib

MD5 = hashlib.md5()

# 连接数据库
def connect_cmt_db():
    db = sqlite3.connect('data.db')
    db.cursor().execute('CREATE TABLE IF NOT EXISTS comments '
                        '(id INTEGER PRIMARY KEY, '
                        'comment TEXT)')
    db.commit()
    return db

def connect_cre_db():
    db = sqlite3.connect('data.db')
    db.cursor().execute('CREATE TABLE IF NOT EXISTS credentials '
                        '(id INTEGER PRIMARY KEY, '
                        'username TEXT, encpswd TEXT, secret TEXT)')
    db.commit()
    return db

# 添加评论
def add_comment(comment):
    db = connect_cmt_db()
    db.cursor().execute('INSERT INTO comments (comment) '
                        'VALUES (?)', (escape(comment),))
    db.commit()

# 得到评论
def get_comments(search_query=None):
    db = connect_cmt_db()
    results = []
    get_all_query = 'SELECT comment FROM comments'
    for (comment,) in db.cursor().execute(get_all_query).fetchall():
        if search_query is None or search_query in comment:
            print(f"Added { comment }")
            results.append(escape(comment))
    return results
    
# Can be modified for local encryption
encrypt_password = lambda pswd: pswd

def init_login(credentials):
    db = connect_cre_db()
    for u, p in credentials:
        MD5.update(p.encode('utf-8'))
        p = str.lower(MD5.hexdigest())
        MD5.update(p.encode('utf-8'))
        s = str.lower(MD5.hexdigest())
        # print(f"Adding {u} with endpswd {p} and secret {s}")
        insert_query = 'INSERT INTO credentials (username, encpswd, secret) VALUES (?, ?, ?)'
        db.cursor().execute(insert_query, (u, p, s))
        db.commit()

def check_login(username, password):
    db = connect_cre_db()
    password = encrypt_password(password)
    
    print(f"Authenticating {username} with {password}")
    msg = ""
    flag = False

    try:
        query = f"SELECT username, encpswd, secret FROM credentials where username = '{username}' and encpswd = '{password}';"
        res = db.cursor().execute(query).fetchall()
        print(res)
        if len(res) != 1:
            msg = "用户名或密码错误，请重试。"
        else:
            flag = True    
            msg = res[0][-1]
        
    except sqlite3.OperationalError as OpErr:
        print(f"Error SQL Operation: {OpErr}")
        msg = "SQL 内部错误"
        return False, msg
    
    except Exception as Err:
        print(f"Error: {Err}")
        msg = "其他错误"
        return False, msg
    
    return flag, msg

init_login([
    ("admin", "@dm1n"),
    ("aiden", "P@ssw0rd")
])

# 启动flask
app = Flask(__name__, static_url_path='/static')

@app.route('/', methods=['GET', 'POST'])
def landing():
    return redirect("/login", code=302)

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        add_comment(request.form['comment'])

    search_query = request.args.get('q')
    search_query = escape(search_query) if search_query is not None else None
    
    comments = get_comments(search_query)
    return render_template('index.html', comments=comments, search_query=search_query)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # username = request.form['username']
        # password = request.form['password']
        # Fix: 对请求数据进行检查并 escape
        username = escape(request.form['username'])
        password = escape(request.form['password'])
        login_res, msg = check_login(username, password)
        
        if login_res:
            print(msg)
            resp = make_response(render_template("index.html"))
            resp.set_cookie('userSecret', bytes(msg, 'utf-8'))
            return resp
        else:
            return render_template('login.html', comment=msg)
    else:
        return render_template('login.html', comment="登录后方可查看内容。")

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    