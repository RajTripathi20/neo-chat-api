"""
Accounting service module.

This module provides functionality for managing user credits,
including checking balances, adding and deducting credits,
and tracking usage.
"""

from src.models.database import db
from fastapi import HTTPException, status
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from src.utils.constants.errors import ERROR_INSUFFICIENT_CREDITS
from src.utils.constants.http import HTTP_PAYMENT_REQUIRED

class CreditManager:
    """
    Credit management service for handling user credits and transactions.
    
    This class provides methods for checking balances, adding and deducting
    credits, and tracking usage across different models.
    """
    
    async def get_balance(self, user_id: str) -> float:
        """
        Get the credit balance for a user.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            float: The user's credit balance.
        """
        # Query the database for the user's balance
        query = """
        SELECT balance FROM users WHERE id = $1
        """
        balance = await db.fetchval(query, user_id)
        
        # If user not found, create a new user with default balance
        if balance is None:
            default_balance = 0  # Default starting balance
            await self.create_user(user_id, default_balance)
            return default_balance
        
        return balance
    
    async def create_user(self, user_id: str, initial_balance: float = 0) -> bool:
        """
        Create a new user with initial balance.
        
        Args:
            user_id: The ID of the user.
            initial_balance: The initial credit balance for the user.
            
        Returns:
            bool: True if the user was created successfully.
        """
        query = """
        INSERT INTO users (id, balance, created_at, updated_at)
        VALUES ($1, $2, $3, $3)
        ON CONFLICT (id) DO NOTHING
        """
        now = datetime.utcnow()
        await db.execute(query, user_id, initial_balance, now)
        return True
    
    async def deduct_credits(
        self, 
        user_id: str, 
        amount: float, 
        description: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Deduct credits from a user's balance.
        
        Args:
            user_id: The ID of the user.
            amount: The amount of credits to deduct.
            description: A description of the transaction.
            metadata: Additional metadata for the transaction.
            
        Returns:
            bool: True if the credits were deducted successfully.
            
        Raises:
            HTTPException: If the user has insufficient credits.
        """
        # Get current balance
        balance = await self.get_balance(user_id)
        
        # Check if sufficient credits
        if balance < amount:
            raise HTTPException(
                status_code=HTTP_PAYMENT_REQUIRED,
                detail=ERROR_INSUFFICIENT_CREDITS
            )
        
        # Update balance
        update_query = """
        UPDATE users
        SET balance = balance - $1, updated_at = $2
        WHERE id = $3
        """
        await db.execute(update_query, amount, datetime.utcnow(), user_id)
        
        # Record transaction
        transaction_id = str(uuid.uuid4())
        transaction_query = """
        INSERT INTO transactions (
            id, user_id, amount, balance, description, 
            metadata, created_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        new_balance = balance - amount
        await db.execute(
            transaction_query,
            transaction_id,
            user_id,
            -amount,  # Negative amount for deduction
            new_balance,
            description,
            metadata or {},
            datetime.utcnow()
        )
        
        return True
    
    async def add_credits(
        self, 
        user_id: str, 
        amount: float, 
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add credits to a user's balance.
        
        Args:
            user_id: The ID of the user.
            amount: The amount of credits to add.
            description: A description of the transaction.
            metadata: Additional metadata for the transaction.
            
        Returns:
            bool: True if the credits were added successfully.
        """
        # Get current balance
        balance = await self.get_balance(user_id)
        
        # Update balance
        update_query = """
        UPDATE users
        SET balance = balance + $1, updated_at = $2
        WHERE id = $3
        """
        await db.execute(update_query, amount, datetime.utcnow(), user_id)
        
        # Record transaction
        transaction_id = str(uuid.uuid4())
        transaction_query = """
        INSERT INTO transactions (
            id, user_id, amount, balance, description, 
            metadata, created_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        new_balance = balance + amount
        await db.execute(
            transaction_query,
            transaction_id,
            user_id,
            amount,
            new_balance,
            description,
            metadata or {},
            datetime.utcnow()
        )
        
        return True
    
    async def get_transactions(
        self, 
        user_id: str, 
        limit: int = 10, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get a list of transactions for a user.
        
        Args:
            user_id: The ID of the user.
            limit: The maximum number of transactions to return.
            offset: The number of transactions to skip.
            
        Returns:
            List[Dict[str, Any]]: A list of transaction records.
        """
        query = """
        SELECT id, amount, balance, description, metadata, created_at
        FROM transactions
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """
        return await db.fetch(query, user_id, limit, offset)
    
    async def get_usage_by_model(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get usage statistics by model for a user.
        
        Args:
            user_id: The ID of the user.
            start_date: The start date for the usage period.
            end_date: The end date for the usage period.
            
        Returns:
            List[Dict[str, Any]]: A list of usage records by model.
        """
        query = """
        SELECT 
            metadata->>'model' as model,
            SUM(ABS(amount)) as total_cost,
            COUNT(*) as request_count
        FROM transactions
        WHERE 
            user_id = $1 
            AND created_at BETWEEN $2 AND $3
            AND metadata->>'model' IS NOT NULL
        GROUP BY metadata->>'model'
        ORDER BY total_cost DESC
        """
        return await db.fetch(query, user_id, start_date, end_date)
    
    async def get_total_usage(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get total usage statistics across all users.
        
        Args:
            start_date: The start date for the usage period.
            end_date: The end date for the usage period.
            
        Returns:
            Dict[str, Any]: Total usage statistics.
        """
        query = """
        SELECT 
            COUNT(DISTINCT user_id) as user_count,
            SUM(ABS(amount)) as total_cost,
            COUNT(*) as request_count
        FROM transactions
        WHERE created_at BETWEEN $1 AND $2
        """
        return await db.fetchrow(query, start_date, end_date)

# Create a singleton instance
credit_manager = CreditManager() 