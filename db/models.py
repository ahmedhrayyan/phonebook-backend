import bcrypt
from datetime import datetime
from sqlalchemy import exc, Column, Integer, VARCHAR, Text, DateTime, LargeBinary
from db import db


class BaseModel:
    def __init__(self):
        ''' Generate new orm object '''
        pass

    def update(self):
        ''' updating element in db  '''
        try:
            db.session.commit()
        except exc.SQLAlchemyError as e:
            db.session.rollback()
            raise e

    def delete(self):
        ''' delete item from db '''
        try:
            db.session.delete(self)
            db.session.commit()
        except exc.SQLAlchemyError as e:
            db.session.rollback()
            raise e

    def insert(self):
        ''' insert item into db '''
        try:
            db.session.add(self)
            db.session.commit()
        except exc.SQLAlchemyError as e:
            db.session.rollback()
            raise e


class User(db.Model, BaseModel):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(VARCHAR, nullable=False)
    email = Column(VARCHAR, nullable=False, unique=True)
    password = Column(LargeBinary, nullable=False)
    avatar = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(
            bytes(password, 'utf-8'), bcrypt.gensalt())

    def checkpw(self, password: str):
        ''' Check if the provided password is equal to user password '''
        return bcrypt.checkpw(bytes(password, 'utf-8'), self.password)

    def set_pw(self, password: str):
        '''
        Set current user passowed.
        password is hashed first before getting assigned to user
        '''
        self.password = bcrypt.hashpw(
            bytes(password, 'utf-8'), bcrypt.gensalt(12))
