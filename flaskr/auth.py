import functools

# Это создает схему элементов с именем 'auth' . Как и объекту application, схеме элементов необходимо знать, где он определен, 
# поэтому __name__ передается в качестве второго аргумента. 
# Параметр url_prefix будет добавляться ко всем URL-адресам, связанным со схемой элементов.

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Код просмотра регистрации
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')    

# bp.before_app_request() регистрирует функцию, которая запускается перед функцией просмотра, независимо от того, какой URL запрашивается. 
# load_logged_in_user проверяет, сохранен ли идентификатор пользователя в сеансе, 
# и получает данные этого пользователя из базы данных, сохраняя их в g.user, 
# который сохраняется в течение всего срока действия запроса. 
# Если нет идентификатора пользователя или если идентификатор не существует, g.user будет None.
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()    

# Чтобы выйти из системы, 
# вам необходимо удалить идентификатор пользователя из сеанса. 
# Тогда load_logged_in_user не будет загружать пользователя при последующих запросах.
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))     

# Для создания, редактирования и удаления записей в блоге пользователю потребуется войти в систему. 
# Для проверки этого можно использовать декоратор для каждого вида, к которому он применяется
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view    