"""
Database migration utilities and demo user creation
"""
import asyncio
import asyncpg
import os
import uuid
import sqlite3
import logging
from dotenv import load_dotenv
from src.models.database import Database

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
db = Database()
logger = logging.getLogger(__name__)
# SQLite implementation


async def create_tables():
    """
    Create all required database tables if they don't exist
    """
    # Create users table
    await db.connect()

    await db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT,
        plan TEXT,
        balance REAL NOT NULL DEFAULT 100.0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create credits table (for backward compatibility)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS credits (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        balance REAL NOT NULL DEFAULT 100.0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Create transactions table
    await db.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        amount REAL NOT NULL,
        balance_after REAL NOT NULL,
        description TEXT NOT NULL,
        model TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Create API keys table
    await db.execute("""
    CREATE TABLE IF NOT EXISTS api_keys (
        id TEXT,
        key TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_used_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Create rate limit table
    await db.execute("""
    CREATE TABLE IF NOT EXISTS rate_limits (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        count INTEGER NOT NULL DEFAULT 0,
        window_start TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Create usage logs table
    await db.execute("""
    CREATE TABLE IF NOT EXISTS usage_logs (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        request_id TEXT NOT NULL,
        model TEXT NOT NULL,
        prompt_tokens INTEGER NOT NULL,
        completion_tokens INTEGER NOT NULL,
        total_tokens INTEGER NOT NULL,
        cost REAL NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Create model pricing table
    await db.execute("""
    CREATE TABLE IF NOT EXISTS model_pricing (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        input_price_per_million_tokens REAL NOT NULL,
        output_price_per_million_tokens REAL NOT NULL,
        context_length INTEGER NOT NULL,
        available BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    logger.info("Database tables created successfully")

async def seed_initial_data():
    """
    Seed the database with initial data
    """
    # Insert model pricing
    models = [
        (
            "neo-reasoning",
            "Neo Reasoning",
            0.55,  # $0.55 per million tokens input
            2.4,   # $2.4 per million tokens output
            128000, # Context length
            True,  # Available
        ),
        (
            "neo-large",
            "Neo Large",
            1.0,   # $1.0 per million tokens input
            3.0,   # $3.0 per million tokens output
            128000, # Context length
            True,  # Available
        )
    ]
    
    for model in models:
        await db.execute("""
        INSERT INTO model_pricing (id, name, input_price_per_million_tokens, output_price_per_million_tokens, context_length, available, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO UPDATE SET
            input_price_per_million_tokens = $3,
            output_price_per_million_tokens = $4,
            context_length = $5,
            available = $6,
            updated_at = CURRENT_TIMESTAMP
        """, *model)
    
    logger.info("Initial data seeded successfully")

async def create_demo_user():
    """Create a demo user with API key and credits"""
    logger.info("Creating demo user...")
    
    # Check if using SQLite
    is_sqlite = DATABASE_URL and DATABASE_URL.startswith("sqlite")
    
    # Create user ID
    user_id = str(uuid.uuid4())
    credit_id = str(uuid.uuid4())
    api_key_id = str(uuid.uuid4())
    api_key = 'sk-neochat-demo'
    
    if is_sqlite:
        # SQLite implementation
        db_path = DATABASE_URL.replace("sqlite:///", "")
        logger.info(f"Using SQLite database at {db_path}")
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Start transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Create user
            cursor.execute(
                "INSERT INTO users (id, email, plan) VALUES (?, ?, ?)",
                (user_id, 'demo@neo-chat.ai', 'free')
            )
            
            # Create credits
            cursor.execute(
                "INSERT INTO credits (id, user_id, balance) VALUES (?, ?, ?)",
                (credit_id, user_id, 100.0)
            )
            
            # Create API key
            cursor.execute(
                "INSERT INTO api_keys (id, user_id, key, name) VALUES (?, ?, ?, ?)",
                (api_key_id, user_id, api_key, 'Demo API Key')
            )
            
            # Commit transaction
            conn.commit()
            
            logger.info(f"Demo user created successfully in SQLite")
            logger.info(f"API Key: {api_key}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating demo user in SQLite: {e}")
        finally:
            conn.close()
    else:
        # PostgreSQL implementation
        try:
            # Connect to database
            conn = await asyncpg.connect(DATABASE_URL)
            
            # Start transaction
            async with conn.transaction():
                # Create user
                await conn.execute('''
                    INSERT INTO users (id, email, plan)
                    VALUES ($1, $2, $3)
                ''', user_id, 'demo@neo-chat.ai', 'free')
                
                # Create credits
                await conn.execute('''
                    INSERT INTO credits (id, user_id, balance)
                    VALUES ($1, $2, $3)
                ''', credit_id, user_id, 100.0)
                
                # Create API key
                await conn.execute('''
                    INSERT INTO api_keys (id, user_id, key, name)
                    VALUES ($1, $2, $3, $4)
                ''', api_key_id, user_id, api_key, 'Demo API Key')
                
                logger.info(f"Demo user created successfully in PostgreSQL")
                logger.info(f"API Key: {api_key}")
        except Exception as e:
            logger.error(f"Error creating demo user in PostgreSQL: {e}")
        finally:
            await conn.close()

async def run_migrations():
    """
    Run all database migrations
    """
    try:
        print("Starting database migrations...")
        await create_tables()
        await seed_initial_data()
        print("All migrations completed successfully")
        logger.info("All migrations completed successfully")
    except Exception as e:
        print(f"Error running migrations: {e}")
        logger.error(f"Error running migrations: {e}")
        raise

async def run_migrations_with_demo_user():
    """
    Run all database migrations and create a demo user
    """
    try:
        print("Starting database migrations with demo user creation...")
        await create_tables()
        await seed_initial_data()
        await create_demo_user()
        print("All migrations and demo user creation completed successfully")
        logger.info("All migrations and demo user creation completed successfully")
    except Exception as e:
        print(f"Error running migrations with demo user: {e}")
        logger.error(f"Error running migrations with demo user: {e}")
        raise

async def delete_all_tables():
    """
    Delete all tables from the database, effectively clearing all data
    """
    print("Starting deletion of all database tables...")
    logger.info("Deleting all database tables...")
    await db.connect()
    
    # Drop tables in reverse order of dependencies
    tables = [
        "usage_logs",
        "rate_limits",
        "api_keys",
        "transactions",
        "credits",
        "model_pricing",
        "users"
    ]
    
    try:
        for table in tables:
            print(f"Dropping table: {table}")
            await db.execute(f"DROP TABLE IF EXISTS {table}")
        print("All database tables deleted successfully")
        logger.info("All database tables deleted successfully")
    except Exception as e:
        print(f"Error deleting database tables: {e}")
        logger.error(f"Error deleting database tables: {e}")
        raise

if __name__ == "__main__":
    # For backward compatibility, allow running this script directly
    import sys
    
    print(f"Running database utility with arguments: {sys.argv}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--create-demo-user":
        # Only create demo user
        print("Creating demo user...")
        asyncio.run(create_demo_user())
    elif len(sys.argv) > 1 and sys.argv[1] == "--full":
        # Run migrations and create demo user
        print("Running full migrations with demo user...")
        asyncio.run(run_migrations_with_demo_user())
    elif len(sys.argv) > 1 and sys.argv[1] == "--delete-all":
        # Delete all tables
        print("Deleting all database tables...")
        asyncio.run(delete_all_tables())
    else:
        # Default: just run migrations
        print("Running standard migrations...")
        asyncio.run(run_migrations()) 