"""Web + browser tools — close two rival-only gaps with NO new model. web_search hits
the open internet (DuckDuckGo, no API key); Browser drives a real Chromium via the
Playwright we already ship (the design renderer), so the agent can look things up AND
test the web apps it builds end-to-end (browse, screenshot, click, fill). Wired into
the tool-use agent (57).

  from web_browse import web_search, Browser
"""
import os


def web_search(query, k=5):
    """Top-k open-web results (title, url, snippet). No API key (DuckDuckGo)."""
    try:
        from ddgs import DDGS
        with DDGS() as d:
            res = list(d.text(query, max_results=k))
        if res:
            return "\n".join(f"- {r.get('title', '')}\n  {r.get('href', '')}\n  "
                             f"{(r.get('body') or '')[:200]}" for r in res)
        return "(no results)"
    except Exception as e:  # noqa: BLE001
        return f"web_search unavailable: {str(e)[:80]}"


class Browser:
    """A lazily-launched headless Chromium the agent drives. One per session."""

    def __init__(self, headless=True):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=headless)
        self.page = self.browser.new_page(viewport={"width": 1280, "height": 800})

    def browse(self, url):
        self.page.goto(url, timeout=20000, wait_until="domcontentloaded")
        txt = self.page.inner_text("body")
        return f"[{self.page.title()}] {txt[:3000]}"

    def screenshot(self, path="/tmp/agent_shot.png"):
        self.page.screenshot(path=path, full_page=True)
        return path                                          # a VLM (58) can then SEE it

    def click(self, selector):
        self.page.click(selector, timeout=6000)
        return f"clicked {selector} -> now at {self.page.url}"

    def fill(self, selector, text):
        self.page.fill(selector, text, timeout=6000)
        return f"filled {selector}"

    def close(self):
        try:
            self.browser.close()
            self._pw.stop()
        except Exception:  # noqa: BLE001
            pass


def selftest():
    ok_search = True
    r = web_search("python enumerate builtin documentation", k=3)
    print(f"  web_search: {'OK' if ('http' in r and 'unavailable' not in r) else 'no-network/blocked'} "
          f"-> {r.splitlines()[0][:60] if r else ''}")
    ok_browser = False
    try:
        import tempfile
        f = os.path.join(tempfile.mkdtemp(), "p.html")
        open(f, "w").write("<title>Demo</title><body><h1>Hello Agent</h1>"
                           "<button id='b'>Click</button></body>")
        b = Browser()
        text = b.browse("file://" + f)
        shot = b.screenshot(os.path.join(os.path.dirname(f), "shot.png"))
        b.close()
        ok_browser = "Hello Agent" in text and os.path.exists(shot)
        print(f"  browser: read page text + screenshot -> {'OK' if ok_browser else 'FAIL'} "
              f"(shot {os.path.getsize(shot)}B)")
    except Exception as e:  # noqa: BLE001
        print(f"  browser: Playwright/chromium issue -> {str(e)[:70]}")
    return ok_browser  # browser is the must-pass; web_search may be network-gated


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
