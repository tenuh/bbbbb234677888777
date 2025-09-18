import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Set
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Table, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.dialects.postgresql import ARRAY
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

# Many-to-many relationship table for user interests
user_interests = Table(
    'user_interests',
    Base.metadata,
    Column('user_id', BigInteger, ForeignKey('users.user_id'), primary_key=True),
    Column('interest_name', String(100), ForeignKey('interests.name'), primary_key=True)
)

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    gender = Column(String(10), nullable=False)  # 'male' or 'female'
    nickname = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)
    age = Column(Integer, nullable=True)
    location = Column(String(100), nullable=True)
    interests = relationship("Interest", secondary=user_interests, back_populates="users")
    total_chats = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    reported_count = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(Text, nullable=True)
    ban_date = Column(DateTime, nullable=True)
    banned_by = Column(BigInteger, nullable=True)  # Admin user_id who banned

class Interest(Base):
    __tablename__ = 'interests'
    
    name = Column(String(100), primary_key=True)
    users = relationship("User", secondary=user_interests, back_populates="interests")
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_a_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    user_b_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    ended_by = Column(BigInteger, nullable=True)  # user_id who ended the session
    is_active = Column(Boolean, default=True)
    report_count = Column(Integer, default=0)
    
    user_a = relationship("User", foreign_keys=[user_a_id])
    user_b = relationship("User", foreign_keys=[user_b_id])

class AdminAction(Base):
    __tablename__ = 'admin_actions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(BigInteger, nullable=False)  # Admin user_id
    action_type = Column(String(50), nullable=False)  # 'ban', 'unban', 'broadcast'
    target_user_id = Column(BigInteger, nullable=True)  # For ban/unban actions
    reason = Column(Text, nullable=True)
    broadcast_message = Column(Text, nullable=True)  # For broadcast actions
    created_at = Column(DateTime, default=datetime.utcnow)

class UserReport(Base):
    __tablename__ = 'user_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    reporter_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    reported_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    chat_session_id = Column(Integer, ForeignKey('chat_sessions.id'), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed = Column(Boolean, default=False)
    reviewed_by = Column(BigInteger, nullable=True)  # Admin user_id
    reviewed_at = Column(DateTime, nullable=True)
    
    reporter = relationship("User", foreign_keys=[reporter_id])
    reported_user = relationship("User", foreign_keys=[reported_id])
    chat_session = relationship("ChatSession")

class BroadcastMessage(Base):
    __tablename__ = 'broadcast_messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(BigInteger, nullable=False)
    message = Column(Text, nullable=False)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

@contextmanager
def get_db():
    """Database session context manager"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()

def init_database():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

def get_user(db, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.user_id == user_id).first()

def create_user(db, user_id: int, username: str, first_name: str, last_name: str, 
               gender: str, nickname: str) -> User:
    """Create a new user"""
    user = User(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        nickname=nickname
    )
    db.add(user)
    db.flush()
    return user

def update_user_activity(db, user_id: int):
    """Update user's last activity"""
    user = get_user(db, user_id)
    if user:
        user.last_active = datetime.utcnow()
        db.flush()

def get_active_users_count(db) -> int:
    """Get count of users active in last 24 hours"""
    since = datetime.utcnow() - timedelta(hours=24)
    return db.query(User).filter(User.last_active >= since).count()

def ban_user(db, user_id: int, admin_id: int, reason: Optional[str] = None):
    """Ban a user"""
    user = get_user(db, user_id)
    if user:
        user.is_banned = True
        user.ban_reason = reason
        user.ban_date = datetime.utcnow()
        user.banned_by = admin_id
        
        # Log admin action
        admin_action = AdminAction(
            admin_id=admin_id,
            action_type='ban',
            target_user_id=user_id,
            reason=reason
        )
        db.add(admin_action)
        db.flush()

def unban_user(db, user_id: int, admin_id: int):
    """Unban a user"""
    user = get_user(db, user_id)
    if user:
        user.is_banned = False
        user.ban_reason = None
        user.ban_date = None
        user.banned_by = None
        
        # Log admin action
        admin_action = AdminAction(
            admin_id=admin_id,
            action_type='unban',
            target_user_id=user_id
        )
        db.add(admin_action)
        db.flush()

def create_chat_session(db, user_a_id: int, user_b_id: int) -> ChatSession:
    """Create a new chat session"""
    session = ChatSession(
        user_a_id=user_a_id,
        user_b_id=user_b_id
    )
    db.add(session)
    db.flush()
    
    # Update chat counts
    user_a = get_user(db, user_a_id)
    user_b = get_user(db, user_b_id)
    if user_a:
        user_a.total_chats += 1
    if user_b:
        user_b.total_chats += 1
    
    return session

def end_chat_session(db, session_id: int, ended_by: int):
    """End a chat session"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        session.is_active = False
        session.ended_at = datetime.utcnow()
        session.ended_by = ended_by
        db.flush()

def get_active_chat_session(db, user_id: int) -> Optional[ChatSession]:
    """Get user's active chat session"""
    return db.query(ChatSession).filter(
        (ChatSession.user_a_id == user_id) | (ChatSession.user_b_id == user_id),
        ChatSession.is_active == True
    ).first()

def create_user_report(db, reporter_id: int, reported_id: int, chat_session_id: Optional[int] = None, reason: Optional[str] = None):
    """Create a user report"""
    report = UserReport(
        reporter_id=reporter_id,
        reported_id=reported_id,
        chat_session_id=chat_session_id,
        reason=reason
    )
    db.add(report)
    
    # Increment reported user's count
    reported_user = get_user(db, reported_id)
    if reported_user:
        reported_user.reported_count += 1
    
    db.flush()
    return report

def get_all_user_ids(db) -> List[int]:
    """Get all user IDs for broadcasting"""
    return [user.user_id for user in db.query(User.user_id).filter(User.is_banned == False).all()]

def create_broadcast_message(db, admin_id: int, message: str) -> BroadcastMessage:
    """Create a broadcast message record"""
    broadcast = BroadcastMessage(
        admin_id=admin_id,
        message=message
    )
    db.add(broadcast)
    db.flush()
    
    # Log admin action
    admin_action = AdminAction(
        admin_id=admin_id,
        action_type='broadcast',
        broadcast_message=message
    )
    db.add(admin_action)
    
    return broadcast

def update_broadcast_stats(db, broadcast_id: int, sent_count: int, failed_count: int):
    """Update broadcast statistics"""
    broadcast = db.query(BroadcastMessage).filter(BroadcastMessage.id == broadcast_id).first()
    if broadcast:
        broadcast.sent_count = sent_count
        broadcast.failed_count = failed_count
        broadcast.completed_at = datetime.utcnow()
        db.flush()