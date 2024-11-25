from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

# В индексе будут показаны все записи, сначала самые последние. 
# ОБЪЕДИНЕНИЕ используется для того, чтобы в результате была доступна информация об авторе из таблицы user
@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)

# Режим создания работает так же, как режим авторизации при регистрации. 
# Либо отображается форма, либо проверяются опубликованные данные и запись добавляется в базу данных, либо отображается сообщение об ошибке.
# Декоратор login_required, о котором вы писали ранее, используется в представлениях блога. 
# Пользователь должен войти в систему, чтобы посетить эти представления, в противном случае он будет перенаправлен на страницу входа.

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')    

# Как в представлениях "Обновить", 
# так и "Удалить" необходимо будет извлекать запись по идентификатору и проверять, 
# соответствует ли автор зарегистрированному пользователю. 
def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

# функция update принимает аргумент id . Который соответствует <int:id> в маршруте. 
# Реальный URL будет выглядеть как /1/update . Flask перехватит 1, убедится, что это значение int, и передаст его в качестве аргумента id

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

# У представления "Удалить" нет собственного шаблона, кнопка "Удалить" является частью update.html и публикуется по URL-адресу /<id>/delete. 
# Поскольку шаблона нет, он будет обрабатывать только метод POST, а затем перенаправлять в индексное представление.

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))