import time
from typing import Optional

from theoriq.utils import TTLCache


def test_set_and_get():
    """Test basic set and get functionality."""
    cache = TTLCache[str](ttl=10, max_size=3)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"


def test_expiration():
    """Test that items expire after the TTL."""
    cache = TTLCache[str](ttl=1, max_size=3)
    cache.set("key1", "value1")
    time.sleep(1.5)  # Wait for the TTL to expire
    assert cache.get("key1") is None


def test_max_size_eviction():
    """Test that the oldest item is evicted when max_size is exceeded."""
    cache = TTLCache[str](ttl=10, max_size=2)
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")  # This should evict "key1"

    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"


def test_overwrite_key():
    """Test that setting a key overwrites its value."""
    cache = TTLCache[str](ttl=10, max_size=3)
    cache.set("key1", "value1")
    cache.set("key1", "new_value1")  # Overwrite "key1"
    assert cache.get("key1") == "new_value1"


def test_delete_key():
    """Test deleting a key from the cache."""
    cache = TTLCache[str](ttl=10, max_size=3)
    cache.set("key1", "value1")
    cache.delete("key1")
    assert cache.get("key1") is None


def test_clear_cache():
    """Test clearing the cache."""
    cache = TTLCache[str](ttl=10, max_size=3)
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.clear()

    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_optional_type():
    """Test that the cache works with Optional types."""
    cache = TTLCache[Optional[int]](ttl=10, max_size=3)
    cache.set("key1", 123)
    cache.set("key2", None)  # None is a valid value

    assert cache.get("key1") == 123
    assert cache.get("key2") is None
