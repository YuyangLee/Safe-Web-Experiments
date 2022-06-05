import os
from flask import Flask, make_response, redirect, render_template, request, escape
import sqlite3
import hashlib

# 连接数据库
def connect_cmt_db():
    db = sqlite3.connect('data.db')
    db.cursor().execute('CREATE TABLE IF NOT EXISTS comments '
                        '(id INTEGER PRIMARY KEY, '
                        'comment TEXT)')
    db.commit()
    return db

# Delete a comment
def connect_cre_db():
    db = sqlite3.connect('data.db')
    db.cursor().execute('CREATE TABLE IF NOT EXISTS credentials '
                        '(id INTEGER PRIMARY KEY, '
                        'username TEXT, encpswd TEXT, secret TEXT)')
    db.commit()
    return db

def auth_admin(username, secret):
    if username != "admin":
        return False
    
    db = connect_cre_db()
    query = f"SELECT username, secret FROM credentials WHERE username = 'admin' and secret = '{ secret }';"
    res = db.cursor().execute(query).fetchall()
    return len(res) == 1

def rm_comment(rm_id, username, secret):
    if not auth_admin(username, secret):
        return False
    
    cmt_db = connect_cmt_db()
    cmt_rm_query = 'DELETE FROM comments WHERE id = ?'
    cmt_db.cursor().execute(cmt_rm_query, (rm_id,))
    cmt_db.commit()
    return True

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
    get_all_query = 'SELECT id, comment FROM comments'
    for (id, comment) in db.cursor().execute(get_all_query).fetchall():
        if search_query is None or search_query in comment:
            print(f"Added { comment }")
            results.append([id, escape(comment)])
    return results
    
# Can be modified for local encryption
encrypt_password = lambda pswd: pswd

def init_login(credentials):
    db = connect_cre_db()
    for u, p in credentials:
        MD5 = hashlib.md5()
        MD5.update(p.encode('utf-8'))
        p = str.lower(MD5.hexdigest())
        MD5.update(p.encode('utf-8'))
        s = str.lower(MD5.hexdigest())
        print(f"Adding {u} with endpswd {p}")
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
        # msg = "SQL 内部错误"
        # Fix: 避免显示 SQL 内部错误信息
        msg = "用户名或密码错误，请重试。"
        return False, msg
    
    except Exception as Err:
        print(f"Error: {Err}")
        msg = "其他错误"
        return False, msg
    
    return flag, msg

init_login([
    ("aiden", "P@ssw0rd"),
    ("admin", "@dm1n"),
])

# 启动flask
app = Flask(__name__, static_url_path='/static')

@app.route('/', methods=['GET', 'POST'])
def landing():
    return redirect("/login", code=302)

@app.route('/admin', methods=['GET'])
def admin():
    username = request.cookies['username']
    secret = request.cookies['userSecret']
    if not auth_admin(username, secret):
        return redirect("/login", code=302)
    return render_template('admin.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'userSecret' not in request.cookies or 'username' not in request.cookies:
        return redirect("/login", code=302)
    
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
            if username == 'admin':
                resp = make_response(redirect("/admin", code=302))
            else:
                resp = make_response(redirect("/index", code=302))
            resp.set_cookie('username', bytes(username, 'utf-8'))
            resp.set_cookie('userSecret', bytes(msg, 'utf-8'))
            return resp
        else:
            return render_template('login.html', comment=msg)
    else:
        return render_template('login.html', comment="登录后方可查看内容。")

@app.route('/admin/rm', methods=['POST'])
def rm_cmt():
    rm_id = request.form['rm_id']
    username = request.cookies['username']
    secret = request.cookies['userSecret']
    rm_comment(rm_id, username, secret)
    return redirect("/admin", code=302)

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    