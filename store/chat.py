import datetime
from store.models.models import Chat, Message


def create_chat(session, name, owner):
    time = datetime.datetime.now()
    chat = Chat(name=name, created_at=time)
    chat.owners.append(owner)
    chat.members.append(owner)
    session.add(chat)
    session.commit()
    return chat


def get_chat(session, **filter_parametres):
    try:
        chat = session.query(Chat).filter_by(**filter_parametres).one()
        return chat
    except:
        return None


def delete_chat(session, chat_id):
    chat_ask = session.query(Chat).filter_by(id=chat_id)
    session.query(Message).filter_by(chat_id=chat_id).delete()
    chat = chat_ask.one()
    [chat.members.remove(user) for user in chat.members]
    [chat.owners.remove(user) for user in chat.owners]
    chat_ask.delete()
    session.commit()
    return True
