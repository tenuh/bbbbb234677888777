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

# Fix common URL issues for Vercel deployment
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Remove unsupported parameters for serverless
if 'channel_binding=' in DATABASE_URL:
    import re
    DATABASE_URL = re.sub(r'[&?]channel_binding=[^&]*', '', DATABASE_URL)

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
    mood = Column(String(50), nullable=True)  # User's current mood emoji
    language = Column(String(10), default='en')  # User's preferred language: 'en' or 'si'
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

class DeveloperMessage(Base):
    """Messages from users to developer/admin"""
    __tablename__ = 'developer_messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    user = relationship("User", foreign_keys=[user_id])

class MutedUser(Base):
    """Users muted by admin in chat - their messages won't reach partner"""
    __tablename__ = 'muted_users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    muted_by = Column(BigInteger, nullable=False)  # Admin ID
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", foreign_keys=[user_id])

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

def get_pending_reports(db):
    """Get all pending user reports"""
    return db.query(UserReport).filter(
        UserReport.reviewed == False
    ).order_by(UserReport.created_at.desc()).all()

def get_banned_users(db):
    """Get all banned users"""
    return db.query(User).filter(
        User.is_banned == True
    ).order_by(User.ban_date.desc()).all()

def update_user_profile(db, user_id: int, field: str, value):
    """Update a specific field in user profile"""
    user = get_user(db, user_id)
    if user:
        if field == 'bio':
            user.bio = value
        elif field == 'age':
            try:
                age = int(value)
                if 18 <= age <= 80:
                    user.age = age
                else:
                    return False
            except ValueError:
                return False
        elif field == 'location':
            user.location = value
        elif field == 'gender':
            if value in ['male', 'female']:
                user.gender = value
            else:
                return False
        elif field == 'nickname':
            if len(value) >= 2 and len(value) <= 20:
                existing = db.query(User).filter(
                    User.nickname == value,
                    User.user_id != user_id
                ).first()
                if existing:
                    return False
                user.nickname = value
            else:
                return False
        
        user.last_active = datetime.utcnow()
        db.flush()
        return True
    return False

def set_user_interests(db, user_id: int, interests_list: List[str]):
    """Set user interests"""
    user = get_user(db, user_id)
    if not user:
        return False
    
    # Clear existing interests
    user.interests.clear()
    
    # Add new interests
    for interest_name in interests_list:
        interest_name = interest_name.strip().lower()
        if interest_name and len(interest_name) <= 50:
            # Get or create interest
            interest = db.query(Interest).filter(
                Interest.name == interest_name
            ).first()
            
            if not interest:
                interest = Interest(name=interest_name)
                db.add(interest)
                db.flush()
            
            user.interests.append(interest)
    
    user.last_active = datetime.utcnow()
    db.flush()
    return True

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

def create_developer_message(db, user_id: int, message: str) -> DeveloperMessage:
    """Create a message from user to developer"""
    dev_msg = DeveloperMessage(
        user_id=user_id,
        message=message
    )
    db.add(dev_msg)
    db.flush()
    return dev_msg

def get_unread_developer_messages(db) -> List[DeveloperMessage]:
    """Get all unread developer messages"""
    return db.query(DeveloperMessage).filter(
        DeveloperMessage.is_read == False
    ).order_by(DeveloperMessage.created_at.desc()).all()

def get_all_developer_messages(db, limit: int = 20) -> List[DeveloperMessage]:
    """Get all developer messages"""
    return db.query(DeveloperMessage).order_by(
        DeveloperMessage.created_at.desc()
    ).limit(limit).all()

def mark_developer_message_read(db, message_id: int):
    """Mark a developer message as read"""
    msg = db.query(DeveloperMessage).filter(DeveloperMessage.id == message_id).first()
    if msg:
        msg.is_read = True
        msg.read_at = datetime.utcnow()
        db.flush()

def mute_user(db, user_id: int, admin_id: int, reason: Optional[str] = None) -> MutedUser:
    """Mute a user - their messages won't reach partner"""
    existing = db.query(MutedUser).filter(
        MutedUser.user_id == user_id,
        MutedUser.is_active == True
    ).first()
    if existing:
        return existing
    
    muted = MutedUser(
        user_id=user_id,
        muted_by=admin_id,
        reason=reason
    )
    db.add(muted)
    db.flush()
    return muted

def unmute_user(db, user_id: int):
    """Unmute a user"""
    muted = db.query(MutedUser).filter(
        MutedUser.user_id == user_id,
        MutedUser.is_active == True
    ).first()
    if muted:
        muted.is_active = False
        db.flush()

def is_user_muted(db, user_id: int) -> bool:
    """Check if user is muted"""
    return db.query(MutedUser).filter(
        MutedUser.user_id == user_id,
        MutedUser.is_active == True
    ).first() is not None

def get_muted_users(db) -> List[MutedUser]:
    """Get all muted users"""
    return db.query(MutedUser).filter(
        MutedUser.is_active == True
    ).order_by(MutedUser.created_at.desc()).all()

def update_user_language(db, user_id: int, language: str) -> bool:
    """Update user's preferred language"""
    user = get_user(db, user_id)
    if user and language in ['en', 'si']:
        user.language = language
        db.flush()
        return True
    return False

def get_user_language(db, user_id: int) -> str:
    """Get user's preferred language"""
    user = get_user(db, user_id)
    return user.language if user and user.language else 'en'