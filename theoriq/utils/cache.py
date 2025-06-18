import time
from collections import OrderedDict
from typing import Generic, Optional, TypeVar

# Define a type variable for generic support
T = TypeVar("T")


class TTLCache(Generic[T]):
    def __init__(self, *, ttl: Optional[int] = None, max_size: int = 100):
        """
        Initialize the cache with a specific time-to-live (TTL) and maximum size.

        :param ttl: Time-to-live for cache items in seconds.
        :param max_size: Maximum number of items in the cache.
        """
        self.ttl = ttl
        self.max_size = max_size
        self.cache: OrderedDict[str, tuple[T, Optional[float]]] = OrderedDict()  # Cache storing (value, expiry_time)

    def set(self, key: str, value: T) -> None:
        """
        Store a key-value pair in the cache.

        :param key: The key to store.
        :param value: The value to store.
        """
        if key in self.cache:
            del self.cache[key]

        expiry_time = time.time() + self.ttl if self.ttl is not None else None
        self.cache[key] = (value, expiry_time)

        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def get(self, key: str) -> Optional[T]:
        """
        Retrieve a value from the cache if it hasn't expired.

        :param key: The key to retrieve.
        :return: The value associated with the key, or None if the key doesn't exist or has expired.
        """
        if key in self.cache:
            value, expiry_time = self.cache[key]
            if expiry_time is None or time.time() < expiry_time:
                return value
            else:
                del self.cache[key]
        return None

    def delete(self, key: str) -> None:
        """
        Remove a key from the cache.

        :param key: The key to remove.
        """
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """
        Clear all items from the cache.
        """
        self.cache.clear()
