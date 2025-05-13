# import datetime
# import sqlalchemy
# from sqlalchemy import orm
#
# from .db_session import SqlAlchemyBase
#
#
# class Comment(SqlAlchemyBase):
#     __tablename__ = 'comments'
#
#     id = sqlalchemy.Column(sqlalchemy.Integer,
#                            primary_key=True, autoincrement=True)
#     content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
#     created_date = sqlalchemy.Column(sqlalchemy.DateTime,
#                                      default=datetime.datetime.now)
#     user_id = sqlalchemy.Column(sqlalchemy.Integer,
#                                 sqlalchemy.ForeignKey("users.id"))
#     user = orm.relationship('User')
#     news = orm.relationship('News')
