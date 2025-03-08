import asyncio
import asyncpg
import os
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

async def init_db():
    """Initialize the database with tables"""
    print("Initializing database...")
    
    # Check if using SQLite
    is_sqlite = DATABASE_URL and DATABASE_URL.startswith("sqlite")
    
    if is_sqlite:
        # SQLite initialization
        db_path = DATABASE_URL.replace("sqlite:///", "")
        print(f"Using SQLite database at {db_path}")
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    plan TEXT NOT NULL DEFAULT 'free',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create credits table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS credits (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    balance REAL NOT NULL DEFAULT 0.0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Create transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT NOT NULL,
                    model TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Create API keys table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    key TEXT UNIQUE NOT NULL,
                    name TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Commit changes
            conn.commit()
            print("SQLite database initialized successfully")
        except Exception as e:
            print(f"Error initializing SQLite database: {e}")
        finally:
            conn.close()
    else:
        # PostgreSQL initialization
        try:
            # Connect to database
            conn = await asyncpg.connect(DATABASE_URL)
            
            # Create users table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    plan TEXT NOT NULL DEFAULT 'free',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            ''')
            
            # Create credits table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS credits (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id),
                    balance NUMERIC(10, 4) NOT NULL DEFAULT 0.0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            ''')
            
            # Create transactions table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id),
                    amount NUMERIC(10, 4) NOT NULL,
                    description TEXT NOT NULL,
                    model TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            ''')
            
            # Create API keys table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id),
                    key TEXT UNIQUE NOT NULL,
                    name TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    last_used_at TIMESTAMPTZ
                )
            ''')
            
            print("PostgreSQL database initialized successfully")
        except Exception as e:
            print(f"Error initializing PostgreSQL database: {e}")
        finally:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(init_db()) 