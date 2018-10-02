import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy import create_engine
import random
import string
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer,
                          BadSignature, SignatureExpired)
Base = declarative_base()

secret_key = ''.join(
    random.choice(string.ascii_uppercase + string.digits)
    for x in list(range(32)))


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    password_hash = Column(String(64))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(secret_key, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            # Valid Token, but expired
            return None
        except BadSignature:
            # Invalid Token
            return None
        user_id = data['id']
        return user_id

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {'name': self.name, 'id': self.id}


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    category_item = relationship('CategoryItem', cascade='all, delete-orphan')

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {'name': self.name, 'id': self.id, 'user_id': self.user_id}


class CategoryItem(Base):
    __tablename__ = 'category_item'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250))
    price = Column(String(8))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'price': self.price,
            'category_id': self.category_id,
            'user_id': self.user_id
        }


engine = create_engine('sqlite:///Catalog.db')
Base.metadata.create_all(engine)
