import bcrypt
from typing import List
from sqlalchemy import Column, Integer, String, DATETIME, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Table
from datetime import datetime

Base = declarative_base()

user_subs = Table(
    "user_subscribers",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("sub_id", Integer, ForeignKey("users.id")),
)  # таблица связи пользователя и подписчиков

user_liked_news = Table(
    "user_liked_news",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("news_id", Integer, ForeignKey("news.id")),
)  # таблица связи новости с лайкнувшими пользователями

user_chats = Table(
    'user_chats',
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("chat_id", Integer, ForeignKey("chats.id"))
)

user_owned_chats = Table(
    'user_owned_chats',
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("chat_id", Integer, ForeignKey("chats.id"))
)


# Фишки для взаимодействия:
# chat.users.append(user)
# chat.messages.append(message)
# message.author_id = user.id


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    login = Column(String, unique=True, nullable=False)
    username = Column(String, unique=False, nullable=False)
    password = Column(String)
    # timestamp последней авторизации пользователя
    last_seen_at = Column(Integer)
    bio = Column(String)
    likes = relationship(
        "News", cascade="all", secondary=user_liked_news, back_populates="liked"
    )
    owned = relationship("Chat", cascade="all",
                         secondary=user_owned_chats, back_populates="owners")

    chats = relationship("Chat", cascade="all",
                         secondary=user_chats, back_populates="members")
    news = relationship("News", backref="author", cascade="all")
    created_at = Column(DATETIME)
    avatar_id = Column(Integer, ForeignKey("avatar.id"))

    def __repr__(self):
        return (
            f"<USER ID: {self.id}, login: {self.login}, created_at: {self.created_at}>"
        )

    def to_json(self):
        obj = {}
        obj["id"] = self.id
        obj["login"] = self.login
        obj["created_at"] = self.created_at
        obj["username"] = self.username
        obj["owned"] = [chat.id for chat in self.owned]
        obj["chats"] = [chat.id for chat in self.chats]
        obj["news"] = [news.id for news in self.news]
        obj['bio'] = self.bio if self.bio else "None"
        obj["avatar"] = self.avatar_id if self.avatar_id else "None"
        return obj

    def change(self, session, **kwargs):
        for name, value in kwargs.items():
            if name in self.__dict__:
                attr = self.__getattribute__(name)
                self.__setattr__(name, value if value else attr)
        session.add(self)
        session.commit()

    def seen_user(self, session):
        time = datetime.now().timestamp()
        self.last_seen_at = int(time)
        session.add(self)
        session.commit()


class Avatar(Base):
    """
    Модель аватарок

    id - id аватарки
    unique_name - уникальное имя аватарки
    mime_type - mime type аватарки
    format - формат аватарки
    user_id - id владельца аватарки
    """

    __tablename__ = 'avatar'
    id = Column(Integer, primary_key=True)
    unique_name = Column(String, unique=True)
    mime_type = Column(String)
    avatar_format = Column(String)
    user_avatar = relationship("User", backref="avatar", cascade="all,delete,save-update")

    def __repr__(self):
        return f'<Avatar>: id: {self.id}, unique_name: {self.unique_name}'

    def change(self, session, **kwargs):
        for name, value in kwargs.items():
            if name in self.__dict__:
                attr = self.__getattribute__(name)
                self.__setattr__(name, value if value else attr)
        session.add(self)
        session.commit()


class News(Base):  # класс новости
    """
    Класс новости для бд

    id: int - id объекта в бд

    author_id: int - id автора новости

    created_at: datetime.datetime- дата создания новости

    title: str - заголовок новости

    text: str - содержание новости
    """

    __tablename__ = "news"

    id = Column(Integer, primary_key=True)  # type: int # id в бд

    # type: int # id автора новости
    author_id = Column(Integer, ForeignKey("users.id"))

    # type: datetime   # timestamp создания новости
    created_at = Column(DATETIME)

    liked = relationship(
        "User", cascade="all", secondary=user_liked_news, back_populates="likes"
    )  # пользователи, лайкнувшие запись

    text = Column(String)  # type: str # содержание новости

    def __repr__(self):
        return f"<NEWS ID: {self.id}, created_at: {self.created_at}>"

    def popularity(self) -> int:
        """
        Функция расчитывающая популярность запси по времени создания и количеству лайков
        """
        now = int(datetime.now().timestamp())
        diff = int(now - self.created_at.timestamp())
        rate = len(self.liked) * 1000 / diff
        return rate

    def to_json(self, likecheck=None):
        obj = {}
        obj["id"] = self.id
        obj["text"] = self.text
        obj["created_at"] = self.created_at
        obj["likes"] = len(self.liked)
        obj["author"] = self.author.to_json()
        obj["liked"] = str(likecheck in self.liked)
        return obj

    def change(self, session, **kwargs):
        for name, value in kwargs.items():
            if name in self.__dict__:
                attr = self.__getattribute__(name)
                self.__setattr__(name, value if value else attr)
        session.add(self)
        session.commit()


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True)

    messages = relationship("Message", backref="chat", cascade="all")

    created_at = Column(DATETIME)

    members: List[User] = relationship("User", cascade="all",
                                       secondary=user_chats, back_populates="chats")

    name = Column(String, nullable=False)

    owners: List[User] = relationship("User", cascade="all",
                                      secondary=user_owned_chats, back_populates="owned")

    def __repr__(self) -> str:
        return f"Chat ID = {self.id}; Name: {self.name}; created_at: {self.created_at}"

    def to_json(self):
        obj = {}
        obj["id"] = self.id
        obj["created_at"] = self.created_at
        obj["name"] = self.name
        obj["messages"] = [msg.to_json()
                           for msg in self.messages]
        obj["members"] = [user.id for user in self.members]
        obj["owners"] = [owner.id for owner in self.owners]
        return obj

    def change(self, session, **kwargs):
        for name, value in kwargs.items():
            if name in self.__dict__:
                attr = self.__getattribute__(name)
                self.__setattr__(name, value if value else attr)
        session.add(self)
        session.commit()


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)

    created_at = Column(DATETIME)

    edited_at = Column(DATETIME)

    chat_id = Column(Integer, ForeignKey("chats.id"))

    content = Column(String, nullable=False)

    author_id: int = Column(Integer, ForeignKey("users.id"))

    def __repr__(self) -> str:
        return f"Message ID = {self.id}; created_at: {self.created_at}; author_id: {self.author_id}"

    def to_json(self):
        obj = {}
        obj["id"] = self.id
        obj["created_at"] = self.created_at
        obj["edited_at"] = self.edited_at if self.edited_at else 'None'
        obj["content"] = self.content
        obj["author_id"] = self.author_id
        obj["chat_id"] = self.chat_id
        return obj

    def change(self, session, **kwargs):
        for name, value in kwargs.items():
            if name in self.__dict__:
                attr = self.__getattribute__(name)
                self.__setattr__(name, value if value else attr)
        session.add(self)
        session.commit()
