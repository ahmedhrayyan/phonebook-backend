from db import db
from sqlalchemy import Column, exc

class BaseModel:
    ''' Helper class witch add basic methods to sub models '''

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

    def format(self):
        ''' return data as a dict witch can be seralized '''
        pass
