from datetime import datetime
from email.message import Message
import os
from typing import List, Optional
from random import choice
import bcrypt
import string
import uvicorn
import fastapi
import hashlib
import JWT_func as jwt_func
from fastapi import Depends, UploadFile, File, Form, Header, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from schemas import *
from store import user as user_store, news as news_store, chat as chat_store, msg as msg_store, session_factory, \
    avatar as avatar_store
from starlette.responses import Response

app = fastapi.FastAPI()


def get_session():
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


@app.post("/register")
def post_register(body: RegisterBase, session: Session = Depends(get_session)):
    user = user_store.create_user(session, body.login, body.password)
    if user:
        token = jwt_func.jwt_generate({"user_id": user.id})
        return token
    else:
        return Response("LoginClaimed", status_code=403)


@app.post("/auth")
def post_auth(body: TokenBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        if jwt_func.jwt_not_expired(body.token):
            user_id = jwt_func.jwt_user_id(body.token)
            user = user_store.get_user(session, id=user_id)
            if user:
                return body.token
            else:
                return Response("WrongToken", status_code=400)
        else:
            user_id = jwt_func.jwt_user_id(body.token)
            user = user_store.get_user(session, id=user_id)
            if user:
                return jwt_func.jwt_update(body.token)
            else:
                return Response("WrongToken", status_code=400)

    else:
        return Response("WrongToken", status_code=400)


@app.post("/login")
def post_login(body: LoginBase, session: Session = Depends(get_session)):
    if user_store.login(session, body.login, body.password):
        user_id = user_store.get_user_id_by_login(session, body.login)
        token = jwt_func.jwt_generate({"user_id": user_id})
        user = user_store.get_user(session, id=user_id)
        return token
    else:
        return Response("IncorrectCredetinials", status_code=403)


@app.post("/profile/my")
def post_profile_my(body: TokenBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        user = user_store.get_user(session, id=user_id)
        if user:
            return user.to_json()
        else:
            return Response("UserNotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


@app.put("/profile/my")
def upd_profile_my(body: ProfileBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        user = user_store.get_user(session, id=user_id)
        if user:
            changes = {}
            if "username" in body.dict():
                if not user_store.get_user(session, username=body.username):
                    changes['username'] = body.username
            if "bio" in body.dict():
                changes['bio'] = body.bio
            if changes:
                user.change(session, **changes)
            return user.to_json()
        else:
            return Response("UserNotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


@app.put('/settings/login')
def update_my_login(body: UpdateLogin, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user = user_store.get_user(session, login=body.new_login)
        if user is None:
            user_id = jwt_func.jwt_user_id(body.token)
            user = user_store.get_user(session, id=user_id)
            user.change(session, login=body.new_login)
            return Response(status_code=200)
    return Response(status_code=400)


@app.put('/settings/password')
def update_my_password(body: UpdatePassword, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        user = user_store.get_user(session, id=user_id)
        if user_store.correct_password(session, user, body.old_password):
            user_store.update_password(session, user, body.new_password)
            return Response(status_code=200)
    return Response(status_code=400)


@app.post("/users/{username}")
def post_profile_my(username: str, body: TokenBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        requested_user = user_store.get_user(session, username=username)
        user_id = jwt_func.jwt_user_id(body.token)
        user = user_store.get_user(session, id=user_id)
        if requested_user:
            response_data = requested_user.to_json()
            response_data["subscribed"] = str(user in user_store.subscribers(
                session, requested_user))
            return response_data
        else:
            return Response("UserNotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


@app.post("/profile/{id}")
def post_profile_id(id: int, body: TokenBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        requested_user = user_store.get_user(session, id=id)
        user_id = jwt_func.jwt_user_id(body.token)
        user = user_store.get_user(session, id=user_id)
        if requested_user:
            response_data = requested_user.to_json()
            response_data["subscribed"] = str(user in user_store.subscribers(
                session, requested_user))
            return response_data
        else:
            return Response("UserNotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


@app.post("/news")
def post_profile_news(body: NewsPostBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        news = news_store.create_news(session, user_id, body.text)
        return Response("News created", status_code=200)
    else:
        return Response("TokenExpired", status_code=403)


@app.delete("/news")
def delete_news(body: NewsDeleteBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        news = news_store.get_news(session, id=body.news_id)[0]
        if news:
            if news.author_id == user_id:
                deleted = news_store.delete_news(session, news.id)
                if deleted:
                    return Response("Success", status_code=200)
                else:
                    return Response("UnknownError", status_code=400)
            else:
                return Response("MissingPermissions", status_code=403)
        else:
            return Response("NewsNotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


@app.put("/news")
def update_news(body: NewsUpdateBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        news = news_store.get_news(session, id=body.news_id)[0]
        if news:
            if news.author_id == user_id:
                updated = news_store.update_news(
                    session, news.id, text=body.text)
                if updated:
                    return Response("Success", status_code=200)
                else:
                    return Response("UnknownError", status_code=400)
            else:
                return Response("MissingPermissions", status_code=403)
        else:
            return Response("NewsNotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


@app.post("/profile/my/news")
def get_profile_news(body: TokenBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        news = news_store.get_news(session, author_id=user_id)
        return [i.to_json(user_store.get_user(session, id=user_id)) for i in news] if news else []
    else:
        return Response("TokenExpired", status_code=403)


@app.post("/profile/{id}/news")
def get_profile_news(id: int, session: Session = Depends(get_session),token: Optional[str] = Header(None)):
    if jwt_func.jwt_validate(token):
        user_id = jwt_func.jwt_user_id(token)
        news = news_store.get_news(session, author_id=id)
        return [i.to_json(user_store.get_user(session, id=user_id)) for i in news] if news else []
    else:
        return Response("TokenExpired", status_code=403)


@app.post("/news/new")
def news_news(body: TokenBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        current_user = user_store.get_user(session, id=user_id)
        if current_user:
            sorted_news = news_store.get_sorted_news(
                session, current_user)
            current_user.seen_user(session)
            return [news.to_json(user_store.get_user(session, id=user_id)) for news in sorted_news]
        else:
            return Response("TokenExpired", status_code=403)
    else:
        return Response("TokenExpired", status_code=403)


@app.post("/profile/my/subscriptions")
def post_my_subscriptions(body: TokenBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        subscriptions = user_store.subscriptions(session, user_id)
        return [user.to_json() for user in subscriptions] if subscriptions else []
    else:
        return Response("TokenExpired", status_code=403)


@app.post("/profile/{id}/subscriptions")
def post_subscriptions(
        id: int, body: TokenBase, session: Session = Depends(get_session)
):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        subscriptions = user_store.subscriptions(session, id)
        return [user.to_json() for user in subscriptions] if subscriptions else []
    else:
        return Response("TokenExpired", status_code=403)


@app.post("/profile/my/subscribers")
def post_my_subscribers(body: TokenBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        subscribers = user_store.subscribers(session, user_id)
        if subscribers:
            ret = []
            for user in subscribers:
                obj = user.to_json()
                obj["subscribed"] = str(user in user_store.subscriptions(
                    session, user_id))
                ret.append(obj)
            return ret
        else:
            ret = []
            return ret
    else:
        return Response("TokenExpired", status_code=403)


@app.post("/profile/{id}/subscribers")
def post_subscribers(
        id: int, body: TokenBase, session: Session = Depends(get_session)
):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        subscribers = user_store.subscribers(session, id)
        if subscribers:
            ret = []
            for user in subscribers:
                obj = user.to_json()
                obj["subscribed"] = str(user in user_store.subscriptions(
                    session, user_id))
                ret.append(obj)
            return ret
        else:
            ret = []
            return ret
    else:
        return Response("TokenExpired", status_code=403)


@app.post("/subscription")
def post_subscribe(body: SubscriptionBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        sub_id = jwt_func.jwt_user_id(body.token)
        is_subbed = user_store.get_user(session, id=sub_id) in user_store.subscribers(
            session, body.user_id)
        if is_subbed:
            return Response("AlreadySubscribed", status_code=403)
        subbed = user_store.subscribe(session, sub_id, body.user_id)
        if subbed:
            return {"subscribed": "True"}
        else:
            return Response("UnknownError", status_code=400)
    else:
        return Response("TokenExpired", status_code=403)


@app.delete("/subscription")
def post_unsubscribe(body: SubscriptionBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        sub_id = jwt_func.jwt_user_id(body.token)
        is_subbed = user_store.get_user(session, id=sub_id) in user_store.subscribers(
            session, body.user_id)
        if not is_subbed:
            return Response("NotSubscribed", status_code=403)
        subbed = user_store.unsubscribe(session, sub_id, body.user_id)
        if subbed:
            return {"subscribed": "False"}
        else:
            return Response("UnknownError", status_code=400)
    else:
        return Response("TokenExpired", status_code=403)


@app.post("/likes")
def post_likes(body: LikeBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        news = news_store.get_news(session, id=body.news_id)[0]
        if news:
            news_store.like_news(session, news, user_id)
            return news.to_json(likecheck=user_store.get_user(session, id=user_id))
        else:
            return Response("NewsNotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


@app.delete("/likes")
def delete_likes(body: LikeBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        news = news_store.get_news(session, id=body.news_id)[0]
        if news:
            news_store.remove_like_news(session, news, user_id)
            return news.to_json(likecheck=user_store.get_user(session, id=user_id))
        else:
            return Response("NewsNotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


@app.get("/")
def get_started():
    return "Started"


@app.post('/avatar')
async def post_avatar(request: Request, image: UploadFile = File(...), token: Optional[str] = Header(None),
                      session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(token):
        user_id = jwt_func.jwt_user_id(token)
        data = await image.read()
        unique_name = ''.join(
            choice(string.digits + string.ascii_lowercase) for i in range(32))
        avatar_format = request.headers['avatar_format']
        mime_type = request.headers['mime_type']
        with open(f'storage/avatars/{unique_name}.{avatar_format}', 'wb') as ava:
            ava.write(data)
            ava.close()

        user = user_store.get_user(session, id=user_id)
        if user.avatar_id is not None:
            avatar = avatar_store.get_avatar(session, id=user.avatar_id)
            avatar.change(session, unique_name=unique_name,
                          mime_type=mime_type, avatar_format=avatar_format)
        else:
            avatar = avatar_store.add_avatar(
                session, unique_name, mime_type, avatar_format)
            user_store.update_avatar_id(session, user_id, avatar.id)

        return Response('Success', status_code=200)
    else:
        return Response("TokenExpired", status_code=403)


@app.get('/avatar/{avatar_id}')
def get_avatar(avatar_id: int, session: Session = Depends(get_session)):
    avatar = avatar_store.get_avatar(session, id=avatar_id)
    path = fr'storage/avatars/{avatar.unique_name}.{avatar.avatar_format}'
    if os.path.exists(path):
        return FileResponse(path, 200, media_type=avatar.mime_type, headers={'avatar_format': avatar.avatar_format,
                                                                             'unique_name': avatar.unique_name})
    else:
        return None


@app.post('/chats')
def create_chat(body: ChatBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        user = user_store.get_user(session, id=user_id)
        chat = chat_store.create_chat(session, name=body.name, owner=user)
        if chat:
            return chat.to_json()
        else:
            return Response("UnexpectedError", status_code=400)
    else:
        return Response("TokenExpired", status_code=403)


@app.put('/chats')
def update_chat(body: ChatInfoBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        user = user_store.get_user(session, id=user_id)
        chat = chat_store.get_chat(session, id=body.chat_id)
        if chat:
            if user in chat.owners:
                chat.change(session, name=body.name)
                return chat.to_json()
            else:
                return Response("MissingPermissions", status_code=403)
        else:
            return Response("ChatNotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


@app.delete('/chats')
def delete_chat(body: ChatDeleteBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        user = user_store.get_user(session, id=user_id)
        chat = chat_store.get_chat(session, id=body.chat_id)
        if chat:
            if user in chat.owners:
                chat_store.delete_chat(session, chat.id)
                return Response("Success", status_code=200)
            else:
                return Response("MissingPermissions", status_code=403)
        else:
            return Response("ChatNotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


@app.post('/chat/{chat_id}')
def get_chat(chat_id: int, body: TokenBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        user = user_store.get_user(session, id=user_id)
        chat = chat_store.get_chat(session, id=chat_id)
        if chat:
            if user in chat.members:
                return chat.to_json()
            else:
                return Response("MissingPermissions", status_code=403)
        else:
            return Response("ChatNotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


@app.post('/chat/{chat_id}/messages')
def post_message(chat_id: int, body: MsgBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        user = user_store.get_user(session, id=user_id)
        chat = chat_store.get_chat(session, id=chat_id)
        if chat:
            if user in chat.members:
                msg_store.send_message(session, chat, user, body.content)
                return chat.to_json()
            else:
                return Response("MissingPermissions", status_code=403)
        else:
            return Response("ChatNotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


@app.post('/chat/{chat_id}/members')
def add_members(chat_id: int, body: MembersBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        user = user_store.get_user(session, id=user_id)
        chat = chat_store.get_chat(session, id=chat_id)
        requested_user = user_store.get_user(session, id=body.member_id)
        if chat and user and requested_user:
            chat.members.append(requested_user)
            session.add(chat)
            session.commit()
            return chat.to_json()
        else:
            return Response("NotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


@app.delete('/chat/{chat_id}/members')
def remove_members(chat_id: int, body: MembersBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        user = user_store.get_user(session, id=user_id)
        chat = chat_store.get_chat(session, id=chat_id)
        requested_user = user_store.get_user(session, id=body.member_id)
        if chat and user and requested_user:
            if user in chat.owners and (requested_user not in chat.owners):
                chat.members.remove(requested_user)
                session.add(chat)
                session.commit()
                return chat.to_json()
            elif user == requested_user:
                chat.members.remove(requested_user)
                if user in chat.owners:
                    chat.owners.remove(user)
                session.add(chat)
                session.commit()
                return chat.to_json()
            else:
                return Response("MissingPermissions", status_code=403)
        else:
            return Response("NotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


@app.put('/chat/{chat_id}/messages')
def edit_message(chat_id: int, body: MsgEditBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        user = user_store.get_user(session, id=user_id)
        chat = chat_store.get_chat(session, id=chat_id)
        if chat:
            if user in chat.members:
                msg = msg_store.get_message(session, id=body.message_id)
                msg.change(session, content=body.content)
                return chat.to_json()
            else:
                return Response("MissingPermissions", status_code=403)
        else:
            return Response("ChatNotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


@app.delete('/chat/{chat_id}/messages')
def delete_message(chat_id: int, body: MsgDeleteBase, session: Session = Depends(get_session)):
    if jwt_func.jwt_validate(body.token):
        user_id = jwt_func.jwt_user_id(body.token)
        user = user_store.get_user(session, id=user_id)
        chat = chat_store.get_chat(session, id=chat_id)
        if chat:
            msg = msg_store.get_message(session, id=body.message_id)
            if user in chat.members and msg.author_id == user_id:
                msg_store.delete_message(session, body.message_id)
                return chat.to_json()
            else:
                return Response("MissingPermissions", status_code=403)
        else:
            return Response("ChatNotFound", status_code=404)
    else:
        return Response("TokenExpired", status_code=403)


if __name__ == "__main__":  # Запуск сервера
    uvicorn.run(app, host="127.0.0.1", port=8000)
