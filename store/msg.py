from store.models.models import Message
from datetime import datetime


def send_message(session, chat, user, content):
    time = datetime.now()
    message = Message(content=content, created_at=time)
    session.add(message)
    session.commit()
    message.author_id = user.id
    message.chat_id = chat.id
    chat.messages.append(message)
    session.add(message, chat)
    session.commit()


def get_message(session, **filter_parametres):
    try:
        chat = session.query(Message).filter_by(**filter_parametres).one()
        return chat
    except:
        return None


def delete_message(session, msg_id):
    session.query(Message).filter_by(id=msg_id).delete()
    session.commit()
    return True
