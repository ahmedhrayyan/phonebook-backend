import bcrypt
from datetime import datetime
from sqlalchemy import exc, Column, Integer, VARCHAR, Text, DateTime, LargeBinary
from sqlalchemy.sql.schema import ForeignKey
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
    contacts = db.relationship(
        'Contact', order_by='desc(Contact.id)', lazy=True, cascade='all')

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


class Contact(db.Model, BaseModel):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    name = Column(VARCHAR, nullable=False)
    email = Column(VARCHAR, nullable=True)
    avatar = Column(Text, nullable=True)
    phones = db.relationship(
        'Phone', backref="contact", order_by='desc(Phone.id)', lazy=True, cascade='all')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    def __init__(self, user_id: int, name: str, email: str = None, avatar: str = None):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.avatar = avatar

class Type(db.Model, BaseModel):
    __tablename__ = "types"
    id = Column(Integer, primary_key=True)
    value = Column(VARCHAR, nullable=False)

    def __init__(self, value: str):
        self.value = value


class Phone(db.Model, BaseModel):
    __tablename__ = "phones"
    id = Column(Integer, primary_key=True)
    value = Column(VARCHAR, nullable=False)
    type_id = Column(Integer, ForeignKey('types.id'), nullable=False)
    type = db.relationship('Type')
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)

    def __init__(self, value: str, type_id: int, contact_id: int):
        self.value = value
        self.type_id = type_id
        self.contact_id = contact_id
