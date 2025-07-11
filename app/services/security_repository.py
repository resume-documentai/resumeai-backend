from app.core.database import database
from app.core.models.sql_models import AuthUser
from app.core.utils.security import hash_password
from typing import Optional

class SecurityRepository:
    def __init__(self):
        self.db = database

    def user_exists(self, email: str) -> bool:
        session = self.db.get_session()
        try:
            user = session.query(
                AuthUser
            ).filter(
                AuthUser.email == email
            ).first()
            
            return user is not None
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_user_by_email(self, email: str) -> Optional[AuthUser]:
        session = self.db.get_session()
        try:
            user = session.query(
                AuthUser
            ).filter(
                AuthUser.email == email
            ).first()
            
            return user
        except Exception as e:
            raise e
        finally:
            session.close()

    def register_user_in_db(self, username: str, email: str, password: str):
        session = self.db.get_session()
        try:
            user = AuthUser(
                username=username,
                email=email,
                password_hash=hash_password(password)
            )
            session.add(user)
            session.commit()

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
