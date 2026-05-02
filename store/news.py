import datetime
from store.models.models import User, News
from . import user


def create_news(session, userId, text):
    created_at = datetime.datetime.now()
    news = News(created_at=created_at, text=text, author_id=userId)
    user = session.query(User).filter_by(id=userId).one()
    news.author = user
    session.add(news)
    session.commit()
    return news


def delete_news(session, newsId):
    news = session.query(News).filter_by(id=newsId)
    this_news = news.one()
    for user in [_ for _ in this_news.liked]:
        this_news.liked.remove(user)
    try:
        news.delete()
        session.commit()
        return True
    except:
        return None


def get_news(session, **filter_parameteres):
    fill = session.query(News)
    if filter_parameteres:
        fill = fill.filter_by(**filter_parameteres)
    news = fill.all()
    return news


def update_news(session, newsId, **news_parameteres):
    try:
        fill = session.query(News).filter_by(id=newsId).one()
        fill.change(session, **news_parameteres)
        return True
    except:
        return None


def like_news(session, news, userId):
    if user.get_user(session, id=userId) in news.liked:
        return True
    news.liked.append(user.get_user(session, id=userId))
    session.add(news)
    session.commit()


def remove_like_news(session, news, userId):
    if user.get_user(session, id=userId) in news.liked:
        news.liked.remove(user.get_user(session, id=userId))
        session.add(news)
        session.commit()


def get_sorted_news(session, user: User):
    all_news = get_news(session)
    news = [news_obj for news_obj in all_news if int(news_obj.created_at.timestamp())
            > (user.last_seen_at if user.last_seen_at else 0)]
    sorted_news = reversed(sorted(news, key=lambda n: n.popularity()))
    return sorted_news
