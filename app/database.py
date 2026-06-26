import os
import aiosqlite
from contextlib import asynccontextmanager
from app.config import Config

@asynccontextmanager
async def get_db():
    db_dir = os.path.dirname(Config.DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    async with aiosqlite.connect(Config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA busy_timeout=30000")
        yield db

async def init_db():
    async with get_db() as db:
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE,
                vk_id INTEGER UNIQUE,
                fullname TEXT NOT NULL,
                phone TEXT,
                birthdate TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Trial bookings
        await db.execute("""
            CREATE TABLE IF NOT EXISTS trial_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                booking_time TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                cancel_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        # Cancel requests
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cancel_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reason TEXT,
                lesson_datetime TEXT,
                cancel_option TEXT,
                photo_attachment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # FSM sessions (если используете)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS fsm_sessions (
                user_key TEXT PRIMARY KEY,
                step TEXT,
                data TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_trial_user ON trial_bookings(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_trial_status ON trial_bookings(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_cancel_user ON cancel_requests(user_id)")
        await db.commit()