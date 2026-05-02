from typing import Union
import store
from store.models.models import *
import datetime
import asyncio


def create_user(session, login, password):
    created_at = datetime.datetime.now()
    bcrypt_pass = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
    user = User(
        login=login, password=bcrypt_pass, created_at=created_at, username=login
    )
    try:
        session.add(user)
        session.commit()
        user = session.query(User).filter_by(login=login).one()
        return user
    except:
        return None


def login(session, login, password):
    user = get_user(session, login=login)
    if user is None:
        return None
    if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        return False
    return True


def get_user(session, **filter_parametres):
    try:
        user = session.query(User).filter_by(**filter_parametres).one()
        return user
    except:
        return None


def get_user_id_by_login(session, login):
    user = get_user(session, login=login)
    return user.id if user else user


def subscribe(session, subscriber: Union[User, int], user: Union[User, int]):
    try:
        insert = user_subs.insert().values(
            user_id=user.id if isinstance(user, User) else user,
            sub_id=subscriber.id if isinstance(
                subscriber, User) else subscriber,
        )
        store.engine.execute(insert)
        return True
    except:
        return None


def unsubscribe(session, subscriber: Union[User, int], user: Union[User, int]):
    try:
        delete = user_subs.delete().where(
            user_subs.c.user_id == (
                user.id if isinstance(user, User) else user),
            user_subs.c.sub_id
            == (subscriber.id if isinstance(subscriber, User) else subscriber),
        )
        store.engine.execute(delete)
        return True
    except:
        return None


def subscriptions(session, user: Union[User, int]):
    user_tuple = (
        session.query(user_subs)
            .filter_by(sub_id=user.id if isinstance(user, User) else user)
            .all()
    )
    users = []
    for subs in user_tuple:
        users.append(get_user(session, id=subs[0]))
    return users


def subscribers(session, user: Union[User, int]):
    user_tuple = (
        session.query(user_subs)
            .filter_by(user_id=user.id if isinstance(user, User) else user)
            .all()
    )
    users = []
    for subs in user_tuple:
        users.append(get_user(session, id=subs[1]))
    return users


def correct_password(session, user, old_password):
    if bcrypt.checkpw(old_password.encode("utf-8"), user.password.encode("utf-8")):
        return True
    return False


def update_password(session, user, new_password):
    bcrypt_pass = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user.change(session, password=bcrypt_pass)


def update_avatar_id(sess, user_id, avatar_id):
    user = sess.query(User).filter_by(id=user_id).one()
    user.avatar_id = avatar_id
    sess.commit()
