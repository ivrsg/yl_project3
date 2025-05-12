import sqlalchemy
from .db_session import SqlAlchemyBase


class Expenses(SqlAlchemyBase):
    __tablename__ = 'expenses'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    users_id = sqlalchemy.Column(sqlalchemy.Integer,
                                 sqlalchemy.ForeignKey("users.id"))
    category = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    sum = sqlalchemy.Column(sqlalchemy.Float, default=0)
    regular = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    first_regular = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    period = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    sum_regular = sqlalchemy.Column(sqlalchemy.Float, nullable=True)
    lim = sqlalchemy.Column(sqlalchemy.Float, nullable=True)
