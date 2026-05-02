from store.models.models import *


def add_avatar(session, unique_name, mime_type, avatar_format):
    avatar = Avatar(unique_name=unique_name, mime_type=mime_type, avatar_format=avatar_format)
    try:
        session.add(avatar)
        session.commit()
        avatar = session.query(Avatar).filter_by(unique_name=unique_name).one()
        return avatar
    except:
        return None


def get_avatar(session, **kwargs):
    try:
        avatar = session.query(Avatar).filter_by(**kwargs).one()
        return avatar
    except:
        return None
