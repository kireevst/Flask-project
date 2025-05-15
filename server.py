from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gameshop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Модели базы данных
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    articles = db.relationship('Article', backref='author', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    release_date = db.Column(db.Date, nullable=False)
    platform = db.Column(db.String(50), nullable=False)


class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image = db.Column(db.String(100), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Processing')
    game = db.relationship('Game', backref='orders')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def save_image(file):
    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None


@app.route('/')
def index():
    news = News.query.order_by(News.date_posted.desc()).limit(3).all()
    featured_games = Game.query.order_by(Game.release_date.desc()).limit(4).all()
    return render_template('index.html', news=news, featured_games=featured_games)


@app.route('/catalog')
def catalog():
    games = Game.query.all()
    return render_template('catalog.html', games=games)


@app.route('/game/<int:game_id>')
def game_details(game_id):
    game = Game.query.get_or_404(game_id)
    return render_template('game_details.html', game=game)


@app.route('/buy/<int:game_id>', methods=['POST'])
@login_required
def buy_game(game_id):
    game = Game.query.get_or_404(game_id)

    existing_order = Order.query.filter_by(user_id=current_user.id, game_id=game.id).first()
    if existing_order:
        flash('Вы уже приобрели эту игру!', 'warning')
        return redirect(url_for('game_details', game_id=game.id))

    new_order = Order(user_id=current_user.id, game_id=game.id)
    db.session.add(new_order)
    db.session.commit()

    flash('Игра успешно приобретена!', 'success')
    return redirect(url_for('game_details', game_id=game.id))


@app.route('/forum')
def forum():
    articles = Article.query.filter_by(is_approved=True).order_by(Article.date_posted.desc()).all()
    return render_template('forum.html', articles=articles)


@app.route('/article/<int:article_id>')
def view_article(article_id):
    article = Article.query.get_or_404(article_id)
    if not article.is_approved and not (current_user.is_authenticated and current_user.is_admin):
        flash('Эта статья еще не одобрена администратором', 'warning')
        return redirect(url_for('forum'))
    return render_template('view_article.html', article=article)


@app.route('/create_article', methods=['GET', 'POST'])
@login_required
def create_article():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        new_article = Article(
            title=title,
            content=content,
            author_id=current_user.id,
            is_approved=False
        )

        db.session.add(new_article)
        db.session.commit()

        flash('Ваша статья отправлена на модерацию!', 'success')
        return redirect(url_for('forum'))

    return render_template('create_article.html')


@app.route('/news')
def news():
    all_news = News.query.order_by(News.date_posted.desc()).all()
    return render_template('news.html', news_list=all_news)


@app.route('/news/<int:news_id>')
def view_news(news_id):
    news_item = News.query.get_or_404(news_id)
    return render_template('view_news.html', news=news_item)


@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    pending_articles = Article.query.filter_by(is_approved=False).count()
    total_orders = Order.query.count()
    total_games = Game.query.count()

    return render_template('admin/dashboard.html',
                           pending_articles=pending_articles,
                           total_orders=total_orders,
                           total_games=total_games)


@app.route('/admin/articles')
@login_required
def admin_articles():
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    articles = Article.query.order_by(Article.date_posted.desc()).all()
    return render_template('admin/articles.html', articles=articles)


@app.route('/admin/article/approve/<int:article_id>')
@login_required
def approve_article(article_id):
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    article = Article.query.get_or_404(article_id)
    article.is_approved = True
    db.session.commit()

    flash('Статья одобрена!', 'success')
    return redirect(url_for('admin_articles'))


@app.route('/admin/article/reject/<int:article_id>')
@login_required
def reject_article(article_id):
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    article = Article.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()

    flash('Статья отклонена и удалена!', 'success')
    return redirect(url_for('admin_articles'))


@app.route('/admin/article/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    article = Article.query.get_or_404(article_id)

    if request.method == 'POST':
        article.title = request.form['title']
        article.content = request.form['content']
        article.is_approved = 'is_approved' in request.form

        db.session.commit()

        flash('Статья успешно обновлена!', 'success')
        return redirect(url_for('admin_articles'))

    return render_template('admin/edit_article.html', article=article)


@app.route('/admin/article/delete/<int:article_id>')
@login_required
def delete_article(article_id):
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    article = Article.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()

    flash('Статья удалена!', 'success')
    return redirect(url_for('admin_articles'))


@app.route('/admin/news')
@login_required
def admin_news():
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    news_list = News.query.order_by(News.date_posted.desc()).all()
    return render_template('admin/news.html', news_list=news_list)


@app.route('/admin/news/add', methods=['GET', 'POST'])
@login_required
def add_news():
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = save_image(request.files['image'])

        new_news = News(
            title=title,
            content=content,
            image=image,
            author_id=current_user.id
        )

        db.session.add(new_news)
        db.session.commit()

        flash('Новость успешно добавлена!', 'success')
        return redirect(url_for('admin_news'))

    return render_template('admin/add_news.html')


@app.route('/admin/news/edit/<int:news_id>', methods=['GET', 'POST'])
@login_required
def edit_news(news_id):
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    news_item = News.query.get_or_404(news_id)

    if request.method == 'POST':
        news_item.title = request.form['title']
        news_item.content = request.form['content']

        if request.files['image']:
            news_item.image = save_image(request.files['image'])

        db.session.commit()

        flash('Новость успешно обновлена!', 'success')
        return redirect(url_for('admin_news'))

    return render_template('admin/edit_news.html', news=news_item)


@app.route('/admin/news/delete/<int:news_id>')
@login_required
def delete_news(news_id):
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    news_item = News.query.get_or_404(news_id)
    db.session.delete(news_item)
    db.session.commit()

    flash('Новость удалена!', 'success')
    return redirect(url_for('admin_news'))


@app.route('/admin/games')
@login_required
def admin_games():
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    games = Game.query.all()
    return render_template('admin/games.html', games=games)


@app.route('/admin/games/add', methods=['GET', 'POST'])
@login_required
def add_game():
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])
        genre = request.form['genre']
        platform = request.form['platform']
        release_date = datetime.strptime(request.form['release_date'], '%Y-%m-%d').date()
        image = save_image(request.files['image'])

        new_game = Game(
            title=title,
            description=description,
            price=price,
            genre=genre,
            platform=platform,
            release_date=release_date,
            image=image
        )

        db.session.add(new_game)
        db.session.commit()

        flash('Игра успешно добавлена в каталог!', 'success')
        return redirect(url_for('admin_games'))

    return render_template('admin/add_game.html')


@app.route('/admin/games/edit/<int:game_id>', methods=['GET', 'POST'])
@login_required
def edit_game(game_id):
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    game = Game.query.get_or_404(game_id)

    if request.method == 'POST':
        game.title = request.form['title']
        game.description = request.form['description']
        game.price = float(request.form['price'])
        game.genre = request.form['genre']
        game.platform = request.form['platform']
        game.release_date = datetime.strptime(request.form['release_date'], '%Y-%m-%d').date()

        if request.files['image']:
            game.image = save_image(request.files['image'])

        db.session.commit()

        flash('Игра успешно обновлена!', 'success')
        return redirect(url_for('admin_games'))

    return render_template('admin/edit_game.html', game=game)


@app.route('/admin/games/delete/<int:game_id>')
@login_required
def delete_game(game_id):
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    game = Game.query.get_or_404(game_id)
    db.session.delete(game)
    db.session.commit()

    flash('Игра удалена из каталога!', 'success')
    return redirect(url_for('admin_games'))


@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('admin/orders.html', orders=orders)


@app.route('/admin/order/update/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        flash('У вас нет прав доступа к этой странице', 'danger')
        return redirect(url_for('index'))

    order = Order.query.get_or_404(order_id)
    order.status = request.form['status']
    db.session.commit()

    flash('Статус заказа обновлен!', 'success')
    return redirect(url_for('admin_orders'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Пароли не совпадают!', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Пользователь с таким именем или email уже существует!', 'danger')
            return redirect(url_for('register'))


        new_user = User(username=username, email=email, password=password)

        db.session.add(new_user)
        db.session.commit()

        flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if not user:
            flash('Неверное имя пользователя или пароль!', 'danger')
            return redirect(url_for('login'))

        login_user(user)

        if user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы.', 'success')
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    user_articles = Article.query.filter_by(author_id=current_user.id).order_by(Article.date_posted.desc()).all()
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    return render_template('profile.html', articles=user_articles, orders=user_orders)


# Обработка ошибок
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                password='1234',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    app.run(debug=True)
