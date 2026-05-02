import datetime
import jwt
from datetime import timezone

JWT_SECRET = "MEGA_SUPER_SECRET_KEY"


def jwt_generate(user_id) -> str:
    if not isinstance(user_id, dict):
        user_id = user_id.dict()
    user_id["exp"] = datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(
        hours=2
    )
    return jwt.encode(user_id, JWT_SECRET, algorithm="HS256")


def jwt_validate(token) -> bool:
    try:
        jwt.decode(token, JWT_SECRET, algorithms="HS256", options={"verify_exp": False})
        return True
    except:
        return False


def jwt_not_expired(token) -> bool:
    try:
        jwt.decode(token, JWT_SECRET, algorithms="HS256")
    except jwt.ExpiredSignatureError:
        return False
    return True


def jwt_update(token):
    old_token = jwt.decode(
        token, JWT_SECRET, algorithms="HS256", options={"verify_exp": False}
    )
    old_token.pop("exp")
    new_token = jwt_generate(old_token)
    return new_token


def jwt_user_id(token) -> int:
    user = jwt.decode(
        token, JWT_SECRET, algorithms="HS256", options={"verify_exp": False}
    )
    return int(user["user_id"])
