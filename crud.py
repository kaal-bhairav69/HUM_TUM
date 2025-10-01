from models import User
from sqlalchemy.orm import Session

def create_user(db: Session, sender_name: str, sender_roll: str, recipient_roll: str):
    user = User(sender_name=sender_name, sender_roll=sender_roll, recipient_roll=recipient_roll)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


