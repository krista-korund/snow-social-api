from typing import Optional
from pydantic import BaseModel


class RegisterBase(BaseModel):
    login: str
    password: str


class LoginBase(BaseModel):
    login: str
    password: str


class TokenBase(BaseModel):
    token: str


class NewsPostBase(TokenBase):
    text: str


class NewsDeleteBase(TokenBase):
    news_id: int


class NewsUpdateBase(TokenBase):
    news_id: int
    text: str


class SubscriptionBase(TokenBase):
    user_id: int


class LikeBase(TokenBase):
    news_id: int


class ProfileBase(TokenBase):
    username: Optional[str]
    bio: Optional[str]


class ChatBase(TokenBase):
    name: str


class MembersBase(TokenBase):
    member_id: int


class ChatInfoBase(ChatBase):
    chat_id: int


class ChatDeleteBase(TokenBase):
    chat_id: int


class MsgBase(TokenBase):
    content: str


class MsgEditBase(MsgBase):
    message_id: int


class MsgDeleteBase(TokenBase):
    message_id: int


class UpdateLogin(TokenBase):
    new_login: str


class UpdatePassword(TokenBase):
    old_password: str
    new_password: str
