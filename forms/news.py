from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired
from sqlalchemy import orm


class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    is_private = BooleanField("Личное")
    submit = SubmitField('Применить')
    # game_title = TextAreaField("Название игры о которой вы хотите написать")
    # game_genre = TextAreaField("Жанр игры о которой вы хотите написать")
    # categories = orm.relationship("Category",
    #                               secondary="association",
    #                               backref="news")
