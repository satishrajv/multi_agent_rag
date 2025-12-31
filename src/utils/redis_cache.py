"""
Redis caching utilities for agent state and semantic caching
"""
import redis
import json
import hashlib
import logging
from typing import Any, Optional
from datetime import timedelta

from ..config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache manager for agent state and semantic caching"""

    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True
        )

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set a key-value pair with optional TTL (in seconds)"""
        try:
            serialized_value = json.dumps(value)
            self.client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {str(e)}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {str(e)}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a key"""
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {str(e)}")
            return False

    def generate_cache_key(self, prefix: str, *args) -> str:
        """Generate a cache key from prefix and arguments"""
        key_parts = [str(arg) for arg in args]
        key_string = ":".join([prefix] + key_parts)
        return key_string

    def generate_semantic_key(self, query: str) -> str:
        """Generate a hash-based key for semantic caching"""
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        return f"semantic:{query_hash}"

    def cache_semantic_result(self, query: str, result: Any, ttl: int = 1800) -> bool:
        """Cache a semantic search result"""
        key = self.generate_semantic_key(query)
        return self.set(key, result, ttl)

    def get_semantic_result(self, query: str) -> Optional[Any]:
        """Get cached semantic search result"""
        key = self.generate_semantic_key(query)
        return self.get(key)

    def cache_agent_state(self, agent_name: str, entity_id: str, state: dict, ttl: int = 3600) -> bool:
        """Cache agent processing state"""
        key = self.generate_cache_key("agent_state", agent_name, entity_id)
        return self.set(key, state, ttl)

    def get_agent_state(self, agent_name: str, entity_id: str) -> Optional[dict]:
        """Get cached agent state"""
        key = self.generate_cache_key("agent_state", agent_name, entity_id)
        return self.get(key)

    def cache_retrieval_results(self, query: str, results: list, ttl: int = 1800) -> bool:
        """Cache RAG retrieval results"""
        key = self.generate_semantic_key(f"retrieval:{query}")
        return self.set(key, results, ttl)

    def get_retrieval_results(self, query: str) -> Optional[list]:
        """Get cached retrieval results"""
        key = self.generate_semantic_key(f"retrieval:{query}")
        return self.get(key)

    def flush_all(self) -> bool:
        """Flush all cache (use with caution)"""
        try:
            self.client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis flush error: {str(e)}")
            return False

    def health_check(self) -> bool:
        """Check if Redis is available"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False


# Global cache instance
redis_cache = RedisCache()
