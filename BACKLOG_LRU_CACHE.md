# Backlog Ticket: Implement Proper LRU Cache for Hover Provider

**Title:** `[Language Server] Implement proper LRU cache for hover provider`
**Team:** CORE
**Priority:** Low
**Estimate:** 2 story points
**Labels:** enhancement, language-server, performance

---

## Problem

The hover provider currently uses a simple dictionary for caching builtin
docstrings, which lacks eviction policy and could theoretically grow unbounded.

**Current Implementation** (CORE-357):

```python
# Simple cache for builtin docstrings (bounded by ~35 builtins × 3 languages ≈ 105 entries max)
# Note: Not a true LRU cache - entries never expire. See CORE-XXX for proper LRU implementation.
_docstring_cache: dict[tuple[str, str, str], str] = {}
```

**Location:** `libs/language-server/legesher_language_server/providers/hover.py:25-27`

**Why this works for now:**

- Max entries: ~35 Python builtins × 3 languages = ~105 entries
- Memory impact: ~1-2 MB max
- Low risk in practice

**Why we should improve it:**

- Comment says "bounded" but relies on external constraint (number of builtins)
- Future language additions would increase cache size
- Misleading for developers (says bounded but has no enforcement)
- Best practice is proper resource management

---

## Solution

Implement a proper LRU (Least Recently Used) cache with explicit size limits and eviction policy.

### Option A: Use functools.lru_cache ⭐ RECOMMENDED

Convert the caching logic into a pure function and use Python's built-in LRU cache:

```python
from functools import lru_cache
import builtins
import inspect

@lru_cache(maxsize=256)
def get_builtin_docstring(name: str, source_lang: str, target_lang: str) -> str | None:
    """Get builtin docstring with automatic LRU caching.

    Args:
        name: Builtin name (e.g., 'print', 'len')
        source_lang: Source language code
        target_lang: Target language code

    Returns:
        Formatted docstring or None if builtin not found
    """
    try:
        builtin_obj = getattr(builtins, name)
        docstring = inspect.getdoc(builtin_obj)

        if not docstring:
            return None

        # Get signature if available
        try:
            sig = inspect.signature(builtin_obj)
            signature_str = f"{name}{sig}"
        except (ValueError, TypeError):
            signature_str = f"{name}(...)"

        # Format as markdown
        content = f"**`{signature_str}`** — Python builtin\\n\\n{docstring}"

        # TODO: When translation API integrated, translate docstring here

        return content

    except (AttributeError, TypeError):
        return None

# Then in HoverProvider._hover_builtin:
async def _hover_builtin(self, name: str) -> str | None:
    """Get hover content for builtin function/class."""
    return get_builtin_docstring(name, self.source_lang, self.target_lang)
```

**Benefits:**

- ✅ Automatic LRU eviction when maxsize exceeded
- ✅ Thread-safe (functools.lru_cache handles locking)
- ✅ Zero manual cache management
- ✅ Standard library solution (no dependencies)
- ✅ Cache statistics available via `.cache_info()`

### Option B: Custom OrderedDict-based LRU

If more control needed:

```python
from collections import OrderedDict
from threading import Lock

class LRUCache:
    """Thread-safe LRU cache with size limit."""

    def __init__(self, maxsize: int = 256):
        self.cache = OrderedDict()
        self.maxsize = maxsize
        self.lock = Lock()

    def get(self, key):
        """Get value, moving to end (most recently used)."""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            return None

    def put(self, key, value):
        """Add value, evicting oldest if at capacity."""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.maxsize:
                self.cache.popitem(last=False)  # Remove oldest

    def size(self):
        """Get current cache size."""
        with self.lock:
            return len(self.cache)

# Module-level cache
_docstring_cache = LRUCache(maxsize=256)

# In _hover_builtin:
cached = _docstring_cache.get(cache_key)
if cached:
    return cached

# ... compute content ...

_docstring_cache.put(cache_key, content)
```

**Benefits:**

- ✅ Full control over eviction policy
- ✅ Can add custom logic (TTL, statistics, etc.)
- ✅ Explicit thread safety

### Option C: Use cachetools library

If adding external dependency is acceptable:

```python
from cachetools import LRUCache
import threading

_docstring_cache = LRUCache(maxsize=256)
_cache_lock = threading.Lock()

# In _hover_builtin:
with _cache_lock:
    if cache_key in _docstring_cache:
        return _docstring_cache[cache_key]

# ... compute ...

with _cache_lock:
    _docstring_cache[cache_key] = content
```

---

## Recommendation

**Use Option A (functools.lru_cache)** because:

- Standard library (no dependencies)
- Simplest implementation
- Automatic thread safety
- Well-tested and performant
- Cache statistics built-in

---

## Testing Requirements

- [ ] Test cache hit/miss behavior
- [ ] Test LRU eviction when maxsize exceeded
- [ ] Test thread safety with concurrent access
- [ ] Benchmark performance (should be ≥ current implementation)
- [ ] Test cache statistics (if using functools.lru_cache)

---

## Performance Considerations

- maxsize=256 is generous (only ~35 builtins exist)
- Allows for future expansion (more languages, more builtins)
- LRU overhead is minimal (O(1) for get/put)
- Thread locking is fast (minimal contention expected)

---

## Migration Path

1. Implement new LRU cache function
2. Add tests for new implementation
3. Update `_hover_builtin` to use new cache
4. Remove old `_docstring_cache` dict
5. Update comment/documentation
6. Run performance benchmarks to verify no regression

---

## Acceptance Criteria

- [ ] Cache has explicit size limit (maxsize=256 or configurable)
- [ ] LRU eviction policy implemented and tested
- [ ] Thread-safe implementation
- [ ] Performance meets or exceeds current implementation (<100ms)
- [ ] Cache hit rate tracked (if possible)
- [ ] Documentation updated

---

## Related Issues

- CORE-357: Original hover provider implementation
- Future: CORE-358, CORE-359 may benefit from similar caching pattern

---

## Estimated Effort

**2-3 hours** (using functools.lru_cache)

- 1 hour: Implementation
- 1 hour: Testing
- 30 min: Documentation/PR

---

## Priority

**Low** - Current implementation works fine for MVP. This is a quality improvement for production readiness.

---

## Notes

This ticket was created as follow-up to CORE-357 code review feedback.
The current simple dict cache is perfectly acceptable for the current scale
(~105 max entries), but implementing proper LRU is a best practice for
long-term maintainability.
