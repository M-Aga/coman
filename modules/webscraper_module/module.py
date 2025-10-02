from __future__ import annotations
from coman.core.base_module import BaseModule
import httpx
from bs4 import BeautifulSoup
class Module(BaseModule):
    name = "webscraper"; description = "Fetch a page title"
    def __init__(self, core):
        super().__init__(core)
        @self.router.get("/title")
        def title(url: str):
            r = httpx.get(url, timeout=10); r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            t = soup.title.string.strip() if soup.title and soup.title.string else "(no title)"
            return {"url": url, "title": t}
