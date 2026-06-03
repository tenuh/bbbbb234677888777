import os
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Set
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Table, BigInteger, Float, text
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
    language = Column(String(10), default='en')  # 'en' or 'si' (Sinhala)
    bio = Column(Text, nullable=True)
    age = Column(Integer, nullable=True)
    location = Column(String(100), nullable=True)
    mood = Column(String(50), nullable=True)  # User's current mood emoji
    interests = relationship("Interest", secondary=user_interests, back_populates="users")
    total_chats = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    reported_count = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(Text, nullable=True)
    ban_date = Column(DateTime, nullable=True)
    banned_by = Column(BigInteger, nullable=True)  # Admin user_id who banned
    is_muted = Column(Boolean, default=False)
    muted_by = Column(BigInteger, nullable=True)
    is_silent_banned = Column(Boolean, default=False)
    silent_banned_by = Column(BigInteger, nullable=True)
    is_locked = Column(Boolean, default=False)
    lock_reason = Column(Text, nullable=True)
    lock_date = Column(DateTime, nullable=True)
    locked_by = Column(BigInteger, nullable=True)
    unlock_points = Column(Float, default=0.0)
    points = Column(Float, default=0.0)
    referral_code = Column(String(16), nullable=True, unique=True)
    referred_by = Column(BigInteger, nullable=True)

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


class SavedChat(Base):
    __tablename__ = 'saved_chats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    partner_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", foreign_keys=[owner_id])
    partner = relationship("User", foreign_keys=[partner_id])


class GiftPackPurchase(Base):
    __tablename__ = 'gift_pack_purchases'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    pack_id = Column(String(50), nullable=False)
    purchased_at = Column(DateTime, default=datetime.utcnow)

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
    """Initialize database tables and add missing columns"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Add missing columns to existing tables (for migrations)
        with engine.connect() as conn:
            # Check and add missing columns to users table
            missing_columns = [
                ("language", "VARCHAR(10) DEFAULT 'en'"),
                ("bio", "TEXT"),
                ("age", "INTEGER"),
                ("location", "VARCHAR(100)"),
                ("mood", "VARCHAR(50)"),
                ("total_chats", "INTEGER DEFAULT 0"),
                ("reported_count", "INTEGER DEFAULT 0"),
                ("is_banned", "BOOLEAN DEFAULT FALSE"),
                ("is_muted", "BOOLEAN DEFAULT FALSE"),
                ("ban_reason", "TEXT"),
                ("ban_date", "TIMESTAMP"),
                ("banned_by", "BIGINT"),
                ("muted_by", "BIGINT"),
                ("is_silent_banned", "BOOLEAN DEFAULT FALSE"),
                ("silent_banned_by", "BIGINT"),
                ("is_locked", "BOOLEAN DEFAULT FALSE"),
                ("lock_reason", "TEXT"),
                ("lock_date", "TIMESTAMP"),
                ("locked_by", "BIGINT"),
                ("unlock_points", "FLOAT DEFAULT 0.0"),
                ("points", "FLOAT DEFAULT 0.0"),
                ("referral_code", "VARCHAR(16)"),
                ("referred_by", "BIGINT"),
            ]
            
            for col_name, col_type in missing_columns:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                    conn.commit()
                except Exception:
                    pass  # Column might already exist or other issue
            
            logger.info("Database migration completed successfully")

            # Create or migrate saved chats table
            try:
                conn.execute(text(
                    """
                    CREATE TABLE IF NOT EXISTS saved_chats (
                        id SERIAL PRIMARY KEY,
                        owner_id BIGINT,
                        partner_id BIGINT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                ))
                conn.commit()

                saved_chat_columns = {
                    row[0]
                    for row in conn.execute(text(
                        "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'saved_chats'"
                    ))
                }

                if 'owner_id' not in saved_chat_columns:
                    conn.execute(text("ALTER TABLE saved_chats ADD COLUMN owner_id BIGINT"))
                    conn.commit()
                    if 'user_id' in saved_chat_columns:
                        conn.execute(text("UPDATE saved_chats SET owner_id = user_id WHERE owner_id IS NULL"))
                        conn.commit()

                if 'partner_id' not in saved_chat_columns:
                    conn.execute(text("ALTER TABLE saved_chats ADD COLUMN partner_id BIGINT"))
                    conn.commit()
                    if 'partner_user_id' in saved_chat_columns:
                        conn.execute(text("UPDATE saved_chats SET partner_id = partner_user_id WHERE partner_id IS NULL"))
                        conn.commit()

                if 'user_id' in saved_chat_columns and 'owner_id' in saved_chat_columns:
                    conn.execute(text("UPDATE saved_chats SET user_id = owner_id WHERE user_id IS NULL AND owner_id IS NOT NULL"))
                    conn.commit()

                if 'partner_user_id' in saved_chat_columns and 'partner_id' in saved_chat_columns:
                    conn.execute(text("UPDATE saved_chats SET partner_user_id = partner_id WHERE partner_user_id IS NULL AND partner_id IS NOT NULL"))
                    conn.commit()

                conn.execute(text("ALTER TABLE saved_chats ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                conn.execute(text("DELETE FROM saved_chats WHERE owner_id IS NULL OR partner_id IS NULL"))
                conn.commit()

                try:
                    conn.execute(text("ALTER TABLE saved_chats ALTER COLUMN owner_id SET NOT NULL"))
                    conn.execute(text("ALTER TABLE saved_chats ALTER COLUMN partner_id SET NOT NULL"))
                    conn.commit()
                except Exception as not_null_error:
                    logger.warning(f"Saved chats NOT NULL migration warning: {not_null_error}")
                    conn.rollback()

                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_saved_chats_owner_id ON saved_chats(owner_id)"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_saved_chats_owner_partner ON saved_chats(owner_id, partner_id)"))
                conn.commit()

                try:
                    conn.execute(text(
                        """
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1
                                FROM pg_constraint
                                WHERE conname = 'fk_saved_chats_owner_id'
                            ) THEN
                                ALTER TABLE saved_chats
                                ADD CONSTRAINT fk_saved_chats_owner_id
                                FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE;
                            END IF;
                        END
                        $$;
                        """
                    ))
                    conn.commit()
                except Exception as owner_fk_error:
                    logger.warning(f"Saved chats owner FK migration warning: {owner_fk_error}")
                    conn.rollback()

                try:
                    conn.execute(text(
                        """
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1
                                FROM pg_constraint
                                WHERE conname = 'fk_saved_chats_partner_id'
                            ) THEN
                                ALTER TABLE saved_chats
                                ADD CONSTRAINT fk_saved_chats_partner_id
                                FOREIGN KEY (partner_id) REFERENCES users(user_id) ON DELETE CASCADE;
                            END IF;
                        END
                        $$;
                        """
                    ))
                    conn.commit()
                except Exception as partner_fk_error:
                    logger.warning(f"Saved chats partner FK migration warning: {partner_fk_error}")
                    conn.rollback()
            except Exception as migration_error:
                logger.error(f"Saved chats migration failed: {migration_error}")
                conn.rollback()
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

def mute_user(db, user_id: int, admin_id: int):
    """Silently mute a user — they can still send messages but nothing is forwarded"""
    user = get_user(db, user_id)
    if user:
        user.is_muted = True
        user.muted_by = admin_id
        admin_action = AdminAction(
            admin_id=admin_id,
            action_type='mute',
            target_user_id=user_id
        )
        db.add(admin_action)
        db.flush()

def unmute_user(db, user_id: int, admin_id: int):
    """Unmute a previously muted user"""
    user = get_user(db, user_id)
    if user:
        user.is_muted = False
        user.muted_by = None
        admin_action = AdminAction(
            admin_id=admin_id,
            action_type='unmute',
            target_user_id=user_id
        )
        db.add(admin_action)
        db.flush()

def get_muted_users(db):
    """Get all muted users"""
    return db.query(User).filter(
        User.is_muted == True
    ).all()

def silent_ban_user(db, user_id: int, admin_id: int):
    """Silently ban a user — no notifications to them or their partner"""
    user = get_user(db, user_id)
    if user:
        user.is_silent_banned = True
        user.silent_banned_by = admin_id
        admin_action = AdminAction(
            admin_id=admin_id,
            action_type='silent_ban',
            target_user_id=user_id
        )
        db.add(admin_action)
        db.flush()

def silent_unban_user(db, user_id: int, admin_id: int):
    """Remove a silent ban from a user"""
    user = get_user(db, user_id)
    if user:
        user.is_silent_banned = False
        user.silent_banned_by = None
        admin_action = AdminAction(
            admin_id=admin_id,
            action_type='silent_unban',
            target_user_id=user_id
        )
        db.add(admin_action)
        db.flush()

def get_silent_banned_users(db):
    """Get all silently banned users"""
    return db.query(User).filter(
        User.is_silent_banned == True
    ).all()

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
        elif field == 'language':
            if value in ['en', 'si']:
                user.language = value
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


def _get_saved_chat_columns(db):
    """Detect saved_chats owner/partner column names for legacy compatibility"""
    rows = db.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'saved_chats'"
    )).fetchall()
    columns = {row[0] for row in rows}

    owner_col = 'owner_id' if 'owner_id' in columns else 'user_id' if 'user_id' in columns else None
    partner_col = 'partner_id' if 'partner_id' in columns else 'partner_user_id' if 'partner_user_id' in columns else None
    return owner_col, partner_col


def _get_saved_chat_column_set(db) -> Set[str]:
    """Get all columns currently present in saved_chats table"""
    rows = db.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'saved_chats'"
    )).fetchall()
    return {row[0] for row in rows}


def get_saved_chat(db, owner_id: int, partner_id: int) -> Optional[SavedChat]:
    """Get one saved chat for owner and partner"""
    owner_col, partner_col = _get_saved_chat_columns(db)
    if not owner_col or not partner_col:
        return None

    query = text(
        f"SELECT id, {owner_col} AS owner_id, {partner_col} AS partner_id, created_at FROM saved_chats "
        f"WHERE {owner_col} = :owner_id AND {partner_col} = :partner_id LIMIT 1"
    )
    row = db.execute(query, {'owner_id': owner_id, 'partner_id': partner_id}).fetchone()
    if not row:
        return None

    record = SavedChat()
    record.id = row[0]
    record.owner_id = row[1]
    record.partner_id = row[2]
    record.created_at = row[3]
    return record


def get_saved_chats_for_owner(db, owner_id: int) -> List[SavedChat]:
    """Get all saved chats for one owner"""
    owner_col, partner_col = _get_saved_chat_columns(db)
    if not owner_col or not partner_col:
        return []

    query = text(
        f"SELECT id, {owner_col} AS owner_id, {partner_col} AS partner_id, created_at FROM saved_chats "
        f"WHERE {owner_col} = :owner_id ORDER BY created_at DESC"
    )
    rows = db.execute(query, {'owner_id': owner_id}).fetchall()

    results = []
    for row in rows:
        record = SavedChat()
        record.id = row[0]
        record.owner_id = row[1]
        record.partner_id = row[2]
        record.created_at = row[3]
        results.append(record)
    return results


def count_saved_chats_for_owner(db, owner_id: int) -> int:
    """Count saved chats for one owner"""
    owner_col, partner_col = _get_saved_chat_columns(db)
    if not owner_col or not partner_col:
        return 0

    query = text(f"SELECT COUNT(*) FROM saved_chats WHERE {owner_col} = :owner_id")
    return db.execute(query, {'owner_id': owner_id}).scalar() or 0


def create_saved_chat(db, owner_id: int, partner_id: int) -> Optional[SavedChat]:
    """Create a saved chat if it does not exist"""
    existing = get_saved_chat(db, owner_id, partner_id)
    if existing:
        return existing

    owner_col, partner_col = _get_saved_chat_columns(db)
    if not owner_col or not partner_col:
        return None

    columns = _get_saved_chat_column_set(db)
    insert_fields = [owner_col, partner_col]
    params = {
        'owner_id': owner_id,
        'partner_id': partner_id,
    }

    if 'user_id' in columns and 'user_id' not in insert_fields:
        insert_fields.append('user_id')
        params['user_id'] = owner_id

    if 'partner_user_id' in columns and 'partner_user_id' not in insert_fields:
        insert_fields.append('partner_user_id')
        params['partner_user_id'] = partner_id

    values_clause = []
    for field in insert_fields:
        if field == owner_col:
            values_clause.append(':owner_id')
        elif field == partner_col:
            values_clause.append(':partner_id')
        else:
            values_clause.append(f':{field}')

    insert_query = text(
        f"INSERT INTO saved_chats ({', '.join(insert_fields)}) VALUES ({', '.join(values_clause)}) RETURNING id, created_at"
    )
    row = db.execute(insert_query, params).fetchone()
    if not row:
        return None

    record = SavedChat()
    record.id = row[0]
    record.owner_id = owner_id
    record.partner_id = partner_id
    record.created_at = row[1]
    return record


def delete_saved_chat(db, owner_id: int, partner_id: int) -> bool:
    """Delete one saved chat"""
    owner_col, partner_col = _get_saved_chat_columns(db)
    if not owner_col or not partner_col:
        return False

    delete_query = text(
        f"DELETE FROM saved_chats WHERE {owner_col} = :owner_id AND {partner_col} = :partner_id"
    )
    result = db.execute(delete_query, {'owner_id': owner_id, 'partner_id': partner_id})
    return result.rowcount > 0


# ─── Referral & Points ───────────────────────────────────────────────────────

def generate_referral_code(user_id: int) -> str:
    return hashlib.sha256(f"ref-{user_id}".encode()).hexdigest()[:8].upper()

def ensure_referral_code(db, user_id: int) -> str:
    user = get_user(db, user_id)
    if not user:
        return ""
    if not user.referral_code:
        code = generate_referral_code(user_id)
        user.referral_code = code
        db.flush()
    return user.referral_code

def get_user_by_referral_code(db, code: str) -> Optional['User']:
    return db.query(User).filter(User.referral_code == code.upper()).first()

def add_points(db, user_id: int, amount: float) -> float:
    user = get_user(db, user_id)
    if user:
        user.points = (user.points or 0.0) + amount
        db.flush()
        return user.points
    return 0.0

def add_unlock_points(db, user_id: int, amount: float):
    """Add unlock points to a locked user. Returns (new_unlock_pts, auto_unlocked)."""
    user = get_user(db, user_id)
    if not user or not user.is_locked:
        return (0.0, False)
    user.unlock_points = (user.unlock_points or 0.0) + amount
    db.flush()
    if user.unlock_points >= 5.0:
        user.is_locked = False
        user.lock_reason = None
        user.lock_date = None
        user.locked_by = None
        user.unlock_points = 0.0
        db.flush()
        return (5.0, True)
    return (user.unlock_points, False)


# ─── Lock / Unlock ────────────────────────────────────────────────────────────

def lock_user(db, user_id: int, admin_id: int, reason: Optional[str] = None):
    user = get_user(db, user_id)
    if user:
        user.is_locked = True
        user.lock_reason = reason
        user.lock_date = datetime.utcnow()
        user.locked_by = admin_id
        user.unlock_points = 0.0
        admin_action = AdminAction(
            admin_id=admin_id, action_type='lock',
            target_user_id=user_id, reason=reason
        )
        db.add(admin_action)
        db.flush()

def unlock_user(db, user_id: int, admin_id: int):
    user = get_user(db, user_id)
    if user:
        user.is_locked = False
        user.lock_reason = None
        user.lock_date = None
        user.locked_by = None
        user.unlock_points = 0.0
        admin_action = AdminAction(
            admin_id=admin_id, action_type='unlock',
            target_user_id=user_id
        )
        db.add(admin_action)
        db.flush()

def get_locked_users(db):
    return db.query(User).filter(User.is_locked == True).order_by(User.lock_date.desc()).all()


# ─── Gift Packs ───────────────────────────────────────────────────────────────

def has_purchased_pack(db, user_id: int, pack_id: str) -> bool:
    return db.query(GiftPackPurchase).filter(
        GiftPackPurchase.user_id == user_id,
        GiftPackPurchase.pack_id == pack_id
    ).first() is not None

def get_user_purchased_packs(db, user_id: int) -> List[str]:
    purchases = db.query(GiftPackPurchase).filter(
        GiftPackPurchase.user_id == user_id
    ).all()
    return [p.pack_id for p in purchases]

def purchase_gift_pack(db, user_id: int, pack_id: str, cost: float) -> bool:
    user = get_user(db, user_id)
    if not user or (user.points or 0.0) < cost:
        return False
    if has_purchased_pack(db, user_id, pack_id):
        return False
    user.points = (user.points or 0.0) - cost
    db.add(GiftPackPurchase(user_id=user_id, pack_id=pack_id))
    db.flush()
    return True
