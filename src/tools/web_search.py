from collections import OrderedDict
from typing import Dict, List, Optional
from ddgs import DDGS


class SearchCache:
    def __init__(self, capacity: int = 50):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: str) -> Optional[List[Dict[str, str]]]:
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key: str, value: List[Dict[str, str]]):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def clear(self):
        self.cache.clear()


_cache = SearchCache()


def search_web(query: str, max_results: int = 5) -> str:
    cached = _cache.get(query)
    if cached is not None:
        return _format_results(cached, cached=True)
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        return f"Search error: {e}"
    results = []
    for r in raw:
        results.append(
            {
                "title": r.get("title", ""),
                "snippet": r.get("body", ""),
                "url": r.get("href", ""),
            }
        )
    _cache.put(query, results)
    return _format_results(results, cached=False)


def _format_results(results: List[Dict[str, str]], cached: bool = False) -> str:
    if not results:
        return "No results found."
    lines = []
    if cached:
        lines.append("(cached results)")
    for i, r in enumerate(results):
        lines.append(f"[{i + 1}] {r['title']}")
        lines.append(f"    {r['snippet']}")
        lines.append(f"    Source: {r['url']}")
    return "\n".join(lines)
