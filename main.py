import flask_login
from flask import Flask, render_template, redirect, abort
from sqlalchemy.sql.operators import from_

from data import db_session
from data.users import User
from data.news import News
from forms.user import RegisterForm
from flask_login import LoginManager, login_required, logout_user, login_user
from forms.login import LoginForm
from forms.news import NewsForm
import requests
from urllib import request

########################################


# работает все кроме изменения новостей


########################################
########################################
# команды для того чтобы скачать все нужные библитеки
# pip install flask
# pip install flask-login
# pip install sqlalchemy
# pip install flask-wtf
########################################
# НАПИСАТЬ ОПИСАНИЕ В inf.html
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'mt19937'


@app.route("/")
def index():
    db_sess = db_session.create_session()
    if flask_login.current_user.is_authenticated:
        # news = db_sess.query(News).filter(
        #     (News.user == flask_login.current_user) | (News.is_private != True), News.approved == True)
        news = db_sess.query(News).filter(News.approved == True)
    else:
        news = db_sess.query(News).filter(News.is_private != True)
    # news = db_sess.query(News).filter(News.is_private != True)
    return render_template("index.html", news=news)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        if flask_login.current_user.is_admin:
            news.approved = True
            news.is_checked = True
        # news.game_title = form.game_title.data
        # news.game_genre = form.game_genre.data
        flask_login.current_user.news.append(news)
        db_sess.merge(flask_login.current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление новости',
                           form=form)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == flask_login.current_user
                                          ).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == flask_login.current_user
                                          ).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html',
                           title='Редактирование новости',
                           form=form
                           )


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id,
                                      News.user == flask_login.current_user
                                      ).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route("/inf")
def inf():
    return render_template('inf.html')


@app.route("/my_blogs/<int:user_id>")
def my_blogs(user_id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.user_id == user_id,
                                      News.user == flask_login.current_user)
    return render_template("my_blogs.html", news=news)


@app.route("/all_blogs")
def all_blogs():
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.approved == True)
    return render_template("index.html", news=news)


@app.route("/admin_mode")
def admin_mode():
    return render_template("admin.html")


@app.route('/news_ban/<int:id>', methods=['GET', 'POST'])
@login_required
def news_ban(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id
                                      ).first()
    if news:
        news.is_banned = True
        news.is_checked = True
        db_sess.commit()
    else:
        abort(404)
    return redirect('/check_commentaries')


@app.route('/news_approve/<int:id>', methods=['GET', 'POST'])
@login_required
def news_approve(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id
                                      ).first()
    if news:
        news.approved = True
        news.is_checked = True
        db_sess.commit()
    else:
        abort(404)
    return redirect('/check_commentaries')


@app.route("/check_commentaries")
def check_commentaries():
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.is_checked == False)
    return render_template("news_check_admin.html", news=news)


# @app.route("/games")
# def games_catalog():
#     pass
#

if __name__ == '__main__':
    db_session.global_init("db/blogs.db")
    db_sess = db_session.create_session()
    # admin = User()
    # admin.is_admin = True
    # admin.name = "kireevst"
    # admin.email = "kireevstepan11@gmail.com"
    # admin.set_password("password")
    # admin.about = ""
    # db_sess.add(admin)
    # db_sess.commit()
    app.run(port=8080, host='127.0.0.1')
