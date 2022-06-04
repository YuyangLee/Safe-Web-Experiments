import os
from flask import Flask, redirect, render_template, request, escape
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
                        'username TEXT, encpswd TEXT)')
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
        print(f"Adding {u} with {p}")
        insert_query = 'INSERT INTO credentials (username, encpswd) VALUES (?, ?)'
        db.cursor().execute(insert_query, (u, p))
        db.commit()

def check_login(username, password):
    db = connect_cre_db()
    password = encrypt_password(password)
    
    print(f"Authenticating {username} with {password}")
    msg = ""
    flag = False

    # SQL query
    # SELECT username, encpswd FROM credentials where username = 'username' or and encpswd = 'aaaa...aaaa'
    # Injection query
    # SELECT username, encpswd FROM credentials where username = 'something'; INSERT INTO credentials (username, encpswd) VALUES ('biden', '5f4dcc3b5aa765d61d8327deb882cf99'); SELECT username from credentials where '1' = '1' or and encpswd = 'aaaa...aaaa'
    # Injection code
    # something'; INSERT INTO credentials (username, encpswd) VALUES ('biden', '5f4dcc3b5aa765d61d8327deb882cf99'); SELECT username from credentials where '1' = '1
    try:
        query = f"SELECT username, encpswd FROM credentials where username = '{username}' and encpswd = '{password}';"
        # res = db.cursor().executescript(query).fetchall()
        # db.cursor().executemany(query, [])
        res = db.cursor().execute(query).fetchall()
        print(res)
        if len(res) != 1:
            msg = "用户名或密码错误，请重试。"
        else:
            flag = True    
        
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
        username = request.form['username']
        password = request.form['password']
        login_res, msg = check_login(username, password)
        
        if login_res:
            return redirect("/index", code=302)
        else:
            return render_template('login.html', comment=msg)
    else:
        return render_template('login.html', comment="登录后方可查看内容。")

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    