import asyncio
import asyncpg
import os
import uuid
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

async def create_demo_user():
    """Create a demo user with API key and credits"""
    print("Creating demo user...")
    
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
        print(f"Using SQLite database at {db_path}")
        
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
            
            print(f"Demo user created successfully in SQLite")
            print(f"API Key: {api_key}")
        except Exception as e:
            conn.rollback()
            print(f"Error creating demo user in SQLite: {e}")
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
                
                print(f"Demo user created successfully in PostgreSQL")
                print(f"API Key: {api_key}")
        except Exception as e:
            print(f"Error creating demo user in PostgreSQL: {e}")
        finally:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(create_demo_user()) 