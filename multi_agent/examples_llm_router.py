"""
Example: Using the LLM Router in multi-agent system.

This demonstrates:
1. Initializing the router
2. Sending one-shot requests
3. Managing conversations
4. Handling errors
5. Checking health
"""
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_basic_usage():
    """Basic usage example."""
    from llm.router import get_request_router
    from keys.manager import get_key_manager
    
    # Initialize with key store
    key_store_path = Path("keys.json")
    if not key_store_path.exists():
        logger.error("keys.json not found. Copy from keys_example.json")
        return
    
    key_manager = get_key_manager(key_store_path=key_store_path)
    router = get_request_router(key_manager=key_manager)
    
    # Health check
    health = router.health_check()
    logger.info(f"System health: {health}")
    
    if not health['healthy']:
        logger.error("System unhealthy, exiting")
        return
    
    # Send one-shot request
    response = router.send_one_shot(
        prompt="Explain what a token bucket rate limiter is in one paragraph.",
        model_preference="gemini-2.5-flash",
        expected_completion_tokens=256
    )
    
    if response['success']:
        logger.info(f"Response received:")
        logger.info(f"  Model: {response['model']}")
        logger.info(f"  Tokens: {response['tokens']}")
        logger.info(f"  Content: {response['content'][:200]}...")
    else:
        logger.error(f"Request failed: {response['error']}")


def example_conversation():
    """Conversation management example."""
    from llm.router import get_request_router
    
    router = get_request_router()
    conv_id = "example_conversation_001"
    
    # First message
    response1 = router.send_chat(
        conv_id=conv_id,
        prompt="What are the key principles of good software architecture?",
        model_preference="gemini-2.5-flash",
        system_prompt="You are a software architecture expert."
    )
    
    if response1['success']:
        logger.info(f"First response: {response1['content'][:200]}...")
        
        # Follow-up question (uses conversation history)
        response2 = router.send_chat(
            conv_id=conv_id,
            prompt="Can you give me an example of the first principle you mentioned?",
            model_preference="gemini-2.5-flash"
        )
        
        if response2['success']:
            logger.info(f"Follow-up response: {response2['content'][:200]}...")
        
        # Get full conversation
        conversation = router.get_conversation(conv_id)
        logger.info(f"Total messages: {len(conversation['messages'])}")
        logger.info(f"Metadata: {conversation['metadata']}")


def example_code_generation():
    """Code generation with Pro model."""
    from llm.router import get_request_router
    
    router = get_request_router()
    
    prompt = """
    Generate a Python function that implements a binary search algorithm.
    Include:
    - Type hints
    - Docstring
    - Error handling
    - Unit test
    """
    
    response = router.send_one_shot(
        prompt=prompt,
        model_preference="gemini-2.5-pro",  # Use Pro for code
        expected_completion_tokens=2048,
        temperature=0.3,  # Lower temperature for code
        system_prompt="You are an expert Python developer. Write clean, idiomatic code."
    )
    
    if response['success']:
        logger.info("Generated code:")
        logger.info(response['content'])
        logger.info(f"\nTokens used: {response['tokens']}")
    else:
        logger.error(f"Code generation failed: {response['error']}")


def example_error_handling():
    """Error handling and rate limiting."""
    from llm.router import get_request_router, AllKeysExhaustedError
    
    router = get_request_router()
    
    for i in range(20):  # Try many requests
        try:
            response = router.send_one_shot(
                prompt=f"Request #{i}: Say hello",
                model_preference="gemini-2.5-flash"
            )
            
            if response['success']:
                logger.info(f"Request {i}: Success")
            else:
                if response.get('error_type') == 'rate_limited':
                    logger.warning(f"Request {i}: Rate limited, backing off...")
                    import time
                    time.sleep(5)
                else:
                    logger.error(f"Request {i}: Error - {response['error']}")
        
        except Exception as e:
            logger.exception(f"Request {i} failed with exception: {e}")


def example_key_monitoring():
    """Monitor key usage and health."""
    from keys.manager import get_key_manager
    from keys.redis_client import get_redis_limiter
    
    manager = get_key_manager()
    redis_limiter = get_redis_limiter()
    
    # Get all key statuses
    statuses = manager.get_all_key_statuses()
    
    logger.info("\nKey Status Report:")
    logger.info("=" * 60)
    
    for status in statuses:
        logger.info(f"\nKey: {status['key_id']}")
        logger.info(f"  Model: {status['model']}")
        logger.info(f"  Active: {status['active']}")
        logger.info(f"  In cooldown: {status['in_cooldown']}")
        
        if status['in_cooldown']:
            logger.info(f"  Cooldown TTL: {status['cooldown_ttl']}s")
        
        rpm_usage = status['rpm_usage']
        logger.info(f"  RPM: {rpm_usage['count']} / {status['rpm_limit']}")
        
        tpm_usage = status['tpm_usage']
        logger.info(f"  TPM: {tpm_usage['used']} / {status['tpm_limit']}")


def example_user_rate_limiting():
    """User rate limiting example."""
    from middleware.rate_limit import get_rate_limiter, RateLimitExceeded
    
    limiter = get_rate_limiter()
    user_id = "test_user_123"
    
    logger.info(f"\nTesting user rate limit for {user_id}")
    
    for i in range(15):
        try:
            limiter.check_rate_limit(user_id)
            logger.info(f"Request {i}: Allowed")
        except RateLimitExceeded as e:
            logger.warning(f"Request {i}: Rate limited - {e}")
            logger.info(f"Retry after: {e.retry_after}s")
            break
    
    # Check status
    status = limiter.get_user_status(user_id)
    logger.info(f"\nUser status:")
    logger.info(f"  Available tokens: {status['available_tokens']:.2f}")
    logger.info(f"  Capacity: {status['capacity']}")
    logger.info(f"  Refill rate: {status['refill_rate']:.2f}/s")


def main():
    """Run all examples."""
    logger.info("=" * 60)
    logger.info("LLM Router Examples")
    logger.info("=" * 60)
    
    # Set up environment
    if not os.getenv('REDIS_URL'):
        os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
    
    if not os.getenv('SECRET_STORE_TYPE'):
        os.environ['SECRET_STORE_TYPE'] = 'env'
    
    try:
        logger.info("\n1. Basic Usage")
        example_basic_usage()
        
        logger.info("\n2. Conversation Management")
        example_conversation()
        
        logger.info("\n3. Code Generation")
        example_code_generation()
        
        logger.info("\n4. Key Monitoring")
        example_key_monitoring()
        
        logger.info("\n5. User Rate Limiting")
        example_user_rate_limiting()
        
        logger.info("\n6. Error Handling")
        example_error_handling()
        
    except Exception as e:
        logger.exception(f"Example failed: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Examples complete!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
