"""
Groq LLM API utilities for AI model calls.
"""

import httpx
import os
import logging
import asyncio
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("API_KEY")

# Retry configuration
MAX_RETRIES = 3
TIMEOUT = 60.0
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 10.0


class GroqAPIError(Exception):
    """Exception raised for Groq API errors"""
    pass


class GroqAuthenticationError(GroqAPIError):
    """Exception raised for authentication failures"""
    pass


class GroqTimeoutError(GroqAPIError):
    """Exception raised for timeout errors"""
    pass


class GroqRateLimitError(GroqAPIError):
    """Exception raised for rate limiting"""
    pass


async def llama_api_call(prompt: str, max_retries: int = MAX_RETRIES) -> str:
    """
    Call Groq API with retry logic and specific error handling.
    
    Args:
        prompt: The prompt to send to the API
        max_retries: Maximum number of retry attempts
        
    Returns:
        The API response content
        
    Raises:
        GroqAuthenticationError: If API key is invalid
        GroqTimeoutError: If request times out
        GroqRateLimitError: If rate limited
        GroqAPIError: For other API errors
    """
    
    # Validate API key
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY environment variable not set")
        raise GroqAuthenticationError("API key not configured. Set API_KEY environment variable.")
    
    if not prompt or not isinstance(prompt, str):
        logger.warning(f"Invalid prompt provided: {type(prompt)}")
        raise ValueError("prompt must be a non-empty string")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2048
    }

    backoff = INITIAL_BACKOFF
    last_error = None

    for attempt in range(max_retries):
        try:
            logger.info(f"Calling Groq API (attempt {attempt + 1}/{max_retries})")
            
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(GROQ_API_URL, headers=headers, json=payload)
                
                # Handle different status codes
                if response.status_code == 401:
                    logger.error("Authentication failed: Invalid API key")
                    raise GroqAuthenticationError("Invalid Groq API key")
                
                elif response.status_code == 429:
                    logger.warning(f"Rate limited on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        wait_time = min(backoff, MAX_BACKOFF)
                        logger.info(f"Rate limit: waiting {wait_time}s before retry")
                        await asyncio.sleep(wait_time)
                        backoff *= 2
                        continue
                    else:
                        raise GroqRateLimitError("Rate limit exceeded. Too many requests.")
                
                elif response.status_code >= 500:
                    logger.warning(f"Server error ({response.status_code}) on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        wait_time = min(backoff, MAX_BACKOFF)
                        logger.info(f"Server error: waiting {wait_time}s before retry")
                        await asyncio.sleep(wait_time)
                        backoff *= 2
                        continue
                    else:
                        raise GroqAPIError(f"Groq API server error: {response.status_code}")
                
                # Successful response
                response.raise_for_status()
                result = response.json()
                
                if "choices" not in result or not result["choices"]:
                    logger.error("Invalid API response: no choices in result")
                    raise GroqAPIError("Invalid response format from Groq API")
                
                content = result["choices"][0]["message"]["content"]
                logger.info("Groq API call successful")
                return content

        except httpx.TimeoutError as e:
            logger.warning(f"Timeout error on attempt {attempt + 1}: {e}")
            last_error = GroqTimeoutError(f"Request timeout after {TIMEOUT}s")
            
            if attempt < max_retries - 1:
                wait_time = min(backoff, MAX_BACKOFF)
                logger.info(f"Timeout: waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)
                backoff *= 2
            continue

        except httpx.RequestError as e:
            logger.warning(f"Request error on attempt {attempt + 1}: {e}")
            last_error = GroqAPIError(f"API request failed: {str(e)}")
            
            if attempt < max_retries - 1:
                wait_time = min(backoff, MAX_BACKOFF)
                logger.info(f"Request error: waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)
                backoff *= 2
            continue

        except (GroqAuthenticationError, GroqRateLimitError, GroqTimeoutError):
            # Re-raise specific known errors without retrying on auth/rate limit
            raise

        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            last_error = GroqAPIError(f"Unexpected error: {str(e)}")
            
            if attempt < max_retries - 1:
                wait_time = min(backoff, MAX_BACKOFF)
                logger.info(f"Unexpected error: waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)
                backoff *= 2
            continue

    # All retries exhausted
    if last_error:
        logger.error(f"All {max_retries} retry attempts failed")
        raise last_error
    else:
        raise GroqAPIError("Failed to call Groq API after all retries")
