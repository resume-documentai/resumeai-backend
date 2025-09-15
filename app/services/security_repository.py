from typing import Optional

from app.core.database import Database
from app.core.models.pydantic_models import UserPreferences
from app.core.models.sql_models import AuthUser, UserProfile
from app.core.utils.security import hash_password

class SecurityRepository:
    def __init__(self, db: Database):
        self.db = db

    def username_exists(self, username: str) -> bool:
        session = self.db.get_session()
        try:
            user = session.query(
                AuthUser
            ).filter(
                AuthUser.username == username
            ).first()
            
            return user is not None
        except Exception as e:
            raise e
        finally:
            session.close()

    def email_exists(self, email: str) -> bool:
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
            
    def get_user(self, username_or_email: str) -> Optional[AuthUser]:
        session = self.db.get_session()
        try:
            user = session.query(
                AuthUser
            ).filter(
                AuthUser.email == username_or_email
            ).first()
            
            if user is not None: return user
            
            user = session.query(
                AuthUser
            ).filter(
                AuthUser.username == username_or_email
            ).first()
            
            return user
        except Exception as e:
            raise e
        finally:
            session.close()

    def register_user_in_db(self,
        username: str,
        email: str,
        password: str
    ):
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

    def get_user_preferences(self, user_id: str) -> Optional[UserProfile]:
        session = self.db.get_session()
        try:
            user_profile = session.query(
                UserProfile
            ).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if user_profile is None:
                user_profile = UserProfile(
                    user_id=user_id,
                    preferences={}
                )
                session.add(user_profile)
                session.commit()
            
            return user_profile
        except Exception as e:
            raise e
        finally:
            session.close()

    def set_user_preferences(self, user_id: str, preferences: UserPreferences):
        session = self.db.get_session()
        try:
            user_profile = session.query(
                UserProfile
            ).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if user_profile:
                user_profile.preferences = preferences.model_dump()
            else:
                user_profile = UserProfile(
                    user_id=user_id,
                    preferences=preferences.model_dump()
                )
                session.add(user_profile)
            
            session.commit()
            return user_profile
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()