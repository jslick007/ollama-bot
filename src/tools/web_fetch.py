import urllib.request
import ssl


def fetch_page(url: str, timeout: int = 10) -> str:
    """Fetch the raw HTML/text of *url*.
    Returns the page content as a UTF‑8 string, or an error message.
    """
    try:
        # Use a default SSL context that ignores certificate verification errors
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(url, timeout=timeout, context=context) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except Exception as e:
        return f"Fetch error: {e}"
