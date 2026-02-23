from dataclasses import dataclass
from typing import Optional
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


@dataclass
class User(UserMixin):
    id: str
    email: str
    password_hash: str

    @staticmethod
    def from_document(doc: Optional[dict]):
        if not doc:
            return None
        return User(id=str(doc.get('_id')), email=doc.get('email'), password_hash=doc.get('password_hash'))

    def verify_password(self, candidate: str) -> bool:
        return check_password_hash(self.password_hash, candidate)

    @staticmethod
    def hash_password(raw: str) -> str:
        return generate_password_hash(raw)
