'Data models'
import transaction
from sqlalchemy import func, Column, ForeignKey, Integer, String, LargeBinary, Unicode, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import column_property, scoped_session, sessionmaker, relationship, synonym
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.types import TypeDecorator
from zope.sqlalchemy import ZopeTransactionExtension
from cryptacular import bcrypt

from auth.libraries.tools import encrypt, decrypt, make_random_string
from auth.parameters import *


db = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()
crypt = bcrypt.BCRYPTPasswordManager()


class CaseInsensitiveComparator(ColumnProperty.Comparator):
    'A case-insensitive SQLAlchemy comparator for unicode columns'

    def __eq__(self, other):
        'Return True if the lowercase of both columns are equal'
        return func.lower(self.__clause_element__()) == func.lower(other)


class Encrypted(TypeDecorator):
    """
    An SQLAlchemy type that encrypts on the way in and decrypts on the way out.
    Please note that the encryption first decodes the value into utf-8, 
    which may inflate N unicode characters to N * 2 bytes.
    """

    impl = LargeBinary

    def process_bind_param(self, value, dialect):
        return encrypt(value)

    def process_result_value(self, value, dialect):
        return decrypt(value)


class LowercaseEncrypted(TypeDecorator):
    """
    An SQLAlchemy type that converts the value to lowercase and 
    encrypts on the way in and decrypts on the way out.
    Please note that the encryption first decodes the value into utf-8, 
    which may inflate N unicode characters to N * 2 bytes.
    """

    impl = LargeBinary

    def process_bind_param(self, value, dialect):
        return encrypt((value or '').lower())

    def process_result_value(self, value, dialect):
        return decrypt(value)


class User(Base):
    'A user'
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = column_property(
        Column(Unicode(USERNAME_LEN_MAX), unique=True), 
        comparator_factory=CaseInsensitiveComparator)
    password_ = Column('password', LargeBinary(60)) # Hash from bcrypt
    @property
    def password(self):
        return self.password_
    @password.setter
    def password(self, password):
        self.password_ = crypt.encode(password)
    password = synonym('password_', descriptor=password)
    nickname = column_property(
        Column(Unicode(NICKNAME_LEN_MAX), unique=True),
        comparator_factory=CaseInsensitiveComparator)
    email = Column(LowercaseEncrypted(EMAIL_LEN_MAX * 2), unique=True)
    is_active = Column(Boolean, default=True)
    is_super = Column(Boolean, default=False)
    rejection_count = Column(Integer, default=0)
    minutes_offset = Column(Integer, default=0)
    when_login = Column(DateTime)
    code = Column(String(CODE_LEN), default=lambda: make_random_string(CODE_LEN))
    sms_addresses = relationship('SMSAddress')

    def __str__(self):
        return "<User(id=%s)>" % self.id

    def check(self, password):
        'Return True if we have a matching password'
        return crypt.check(self.password, password)


class User_(Base):
    'An unconfirmed change to a user account'
    __tablename__ = 'users_'
    id = Column(Integer, primary_key=True)
    username = column_property(
        Column(Unicode(USERNAME_LEN_MAX)), 
        comparator_factory=CaseInsensitiveComparator)
    password_ = Column('password', LargeBinary(60)) # Hash from bcrypt
    @property
    def password(self):
        return self.password_
    @password.setter
    def password(self, password):
        self.password_ = crypt.encode(password)
    password = synonym('password_', descriptor=password)
    nickname = column_property(
        Column(Unicode(NICKNAME_LEN_MAX)), 
        comparator_factory=CaseInsensitiveComparator)
    email = Column(LowercaseEncrypted(EMAIL_LEN_MAX * 2))
    user_id = Column(ForeignKey('users.id'))
    ticket = Column(String(TICKET_LEN), unique=True)
    when_expired = Column(DateTime)

    def __str__(self):
        return "<User_(id=%s)>" % self.id


class SMSAddress(Base):
    'An SMS address'
    __tablename__ = 'sms_addresses'
    id = Column(Integer, primary_key=True)
    email = Column(LowercaseEncrypted(EMAIL_LEN_MAX * 2))
    user_id = Column(ForeignKey('users.id'))
    is_active = Column(Boolean, default=False)

    def __str__(self):
        return "<SMSAddress(id=%s)>" % self.id


def initialize_sql(engine):
    'Create tables and insert data'
    # Create tables
    db.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    # If the tables are empty,
    if not db.query(User).count():
        # Prepare data
        userPacks = [
            (u'admin', make_random_string(PASSWORD_LEN_MAX), u'Admin', u'admin@example.com', True),
            (u'user', make_random_string(PASSWORD_LEN_MAX), u'User', u'user@example.com', False), 
        ]
        # Insert data
        userTemplate = '\nUsername\t%s\nPassword\t%s\nNickname\t%s\nEmail\t\t%s'
        for username, password, nickname, email, is_super in userPacks:
            print userTemplate % (username, password, nickname, email)
            db.add(User(username=username, password=password, nickname=nickname, email=email, is_super=is_super))
        print
        transaction.commit()
