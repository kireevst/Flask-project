import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class News(SqlAlchemyBase):
    __tablename__ = 'news'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    likes = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    dislikes = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    is_checked = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    is_banned = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    approved = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    # game_title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    # game_genre = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user = orm.relationship('User')
    comments = orm.relationship('Comments', back_populates='news')
    # comments = orm.relationship('Comment')
