import os
import asyncpg
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
import sqlite3
import json

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

class Database:
    """Database connection manager"""
    def __init__(self):
        self.pool = None
        self.is_sqlite = DATABASE_URL and DATABASE_URL.startswith("sqlite")
        self.sqlite_conn = None
    
    async def connect(self):
        """Connect to the database"""
        if self.is_sqlite:
            # SQLite connection for local development
            db_path = DATABASE_URL.replace("sqlite:///", "")
            self.sqlite_conn = sqlite3.connect(db_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            print(f"Connected to SQLite database at {db_path}")
        else:
            # PostgreSQL connection for production
            if not self.pool:
                self.pool = await asyncpg.create_pool(DATABASE_URL)
    
    async def disconnect(self):
        """Disconnect from the database"""
        if self.is_sqlite and self.sqlite_conn:
            self.sqlite_conn.close()
            self.sqlite_conn = None
        elif self.pool:
            await self.pool.close()
            self.pool = None
    
    async def execute(self, query: str, *args, **kwargs):
        """Execute a query"""
        if self.is_sqlite:
            # SQLite execution
            cursor = self.sqlite_conn.cursor()
            cursor.execute(query, args or kwargs)
            self.sqlite_conn.commit()
            return cursor.rowcount
        else:
            # PostgreSQL execution
            if not self.pool:
                await self.connect()
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args, **kwargs)
    
    async def fetch(self, query: str, *args, **kwargs) -> List[Dict[str, Any]]:
        """Fetch multiple rows"""
        if self.is_sqlite:
            # SQLite fetch
            cursor = self.sqlite_conn.cursor()
            cursor.execute(query, args or kwargs)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        else:
            # PostgreSQL fetch
            if not self.pool:
                await self.connect()
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *args, **kwargs)
                return [dict(row) for row in rows]
    
    async def fetchrow(self, query: str, *args, **kwargs) -> Optional[Dict[str, Any]]:
        """Fetch a single row"""
        if self.is_sqlite:
            # SQLite fetchrow
            cursor = self.sqlite_conn.cursor()
            cursor.execute(query, args or kwargs)
            row = cursor.fetchone()
            return dict(row) if row else None
        else:
            # PostgreSQL fetchrow
            if not self.pool:
                await self.connect()
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *args, **kwargs)
                return dict(row) if row else None
    
    async def fetchval(self, query: str, *args, **kwargs):
        """Fetch a single value"""
        if self.is_sqlite:
            # SQLite fetchval
            cursor = self.sqlite_conn.cursor()
            cursor.execute(query, args or kwargs)
            row = cursor.fetchone()
            return row[0] if row else None
        else:
            # PostgreSQL fetchval
            if not self.pool:
                await self.connect()
            async with self.pool.acquire() as conn:
                return await conn.fetchval(query, *args, **kwargs)

# Create a singleton instance
db = Database() 