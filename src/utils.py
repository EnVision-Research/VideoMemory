#!/usr/bin/env python3
"""
Utility functions for the VideoMemory project.
"""

import time
import logging

logger = logging.getLogger(__name__)


def retry_with_backoff(operation_name: str, max_retries: int, initial_delay: float, operation_func, *args, **kwargs):
    """
    Generic retry function with exponential backoff.
    
    Args:
        operation_name: Name of the operation for logging
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        operation_func: Function to execute
        *args, **kwargs: Arguments to pass to the operation function
        
    Returns:
        Result of the operation function
        
    Raises:
        Exception: If all retry attempts fail
    """
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            return operation_func(*args, **kwargs)
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"⚠️  {operation_name} attempt {attempt + 1} failed: {e}")
                logger.info(f"   Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                logger.error(f"❌ {operation_name} failed after {max_retries} attempts")
                raise
