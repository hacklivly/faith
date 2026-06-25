"""
Isabella - web agent.

Selenium-based browser automation. Real DOM interaction —
read page content, fill forms, click elements, extract data.
"""
import time
import urllib.parse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

_driver = None


def _get_driver():
    """Get or create a persistent Chrome browser instance."""
    global _driver
    if _driver is not None:
        try:
            _driver.title  # check if still alive
            return _driver
        except Exception:
            _driver = None

    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    # Keep browser open after script ends
    opts.add_experimental_option("detach", True)

    _driver = webdriver.Chrome(options=opts)
    _driver.implicitly_wait(5)
    return _driver


def _safe(func):
    """Run a function, return result or error string."""
    try:
        return func()
    except Exception as e:
        return f"Failed: {e}"


# ═══════════════════════════════════════════════════════════
# NAVIGATION
# ═══════════════════════════════════════════════════════════

def goto(url: str) -> str:
    """Navigate to a URL."""
    if not url.startswith("http"):
        url = "https://" + url
    driver = _get_driver()
    driver.get(url)
    return f"Opened {driver.title or url}"


def google(query: str) -> str:
    """Google search and return top results."""
    driver = _get_driver()
    driver.get(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
    time.sleep(1.5)
    results = []
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, "h3")[:5]
        for el in elements:
            title = el.text.strip()
            if title:
                results.append(title)
    except Exception:
        pass
    return f"Google results for '{query}': " + " | ".join(results) if results else f"Searched: {query}"


def youtube_play(query: str) -> str:
    """Search YouTube and play the first video."""
    driver = _get_driver()
    driver.get(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
    try:
        WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "ytd-video-renderer a#video-title"))
        ).click()
        return f"Playing '{query}' on YouTube"
    except Exception:
        # Fallback: click first thumbnail
        try:
            driver.find_element(By.CSS_SELECTOR, "a#video-title").click()
            return f"Playing '{query}' on YouTube"
        except Exception as e:
            return f"Searched but couldn't auto-play: {e}"


def read_page() -> str:
    """Extract main text content from current page."""
    driver = _get_driver()
    try:
        # Try article/main content first
        for selector in ["article", "main", "[role='main']", "#content", ".content"]:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                text = elements[0].text.strip()
                if len(text) > 100:
                    return text[:3000]
        # Fallback: body text
        body = driver.find_element(By.TAG_NAME, "body").text
        return body[:3000] if body else "Page appears empty"
    except Exception as e:
        return f"Failed to read page: {e}"


def get_page_title() -> str:
    """Get current page title and URL."""
    driver = _get_driver()
    return f"{driver.title} — {driver.current_url}"


def read_links() -> str:
    """Get all visible links on page."""
    driver = _get_driver()
    links = driver.find_elements(By.TAG_NAME, "a")
    results = []
    for link in links[:20]:
        text = link.text.strip()
        href = link.get_attribute("href") or ""
        if text and href.startswith("http"):
            results.append(f"{text} → {href}")
    return "\n".join(results) if results else "No links found"


# ═══════════════════════════════════════════════════════════
# INTERACTION
# ═══════════════════════════════════════════════════════════

def click_element(text: str) -> str:
    """Click an element by its visible text."""
    driver = _get_driver()
    try:
        el = driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
        el.click()
        return f"Clicked: {text}"
    except Exception:
        # Try button/link with matching text
        for tag in ["button", "a", "input[type='submit']"]:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, tag)
                for el in elements:
                    if text.lower() in (el.text or el.get_attribute("value") or "").lower():
                        el.click()
                        return f"Clicked: {text}"
            except Exception:
                continue
        return f"Could not find element with text: {text}"


def click_selector(css_selector: str) -> str:
    """Click an element by CSS selector."""
    driver = _get_driver()
    try:
        el = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
        )
        el.click()
        return f"Clicked: {css_selector}"
    except Exception as e:
        return f"Failed: {e}"


def fill_input(selector: str, text: str) -> str:
    """Fill a text input by CSS selector or name."""
    driver = _get_driver()
    try:
        # Try CSS selector first
        el = driver.find_element(By.CSS_SELECTOR, selector)
    except Exception:
        try:
            el = driver.find_element(By.NAME, selector)
        except Exception:
            try:
                el = driver.find_element(By.ID, selector)
            except Exception as e:
                return f"Input not found: {e}"
    el.clear()
    el.send_keys(text)
    return f"Filled '{selector}' with: {text[:50]}"


def submit_form(selector: str = "form") -> str:
    """Submit a form."""
    driver = _get_driver()
    try:
        form = driver.find_element(By.CSS_SELECTOR, selector)
        form.submit()
        return "Form submitted"
    except Exception as e:
        return f"Failed: {e}"


def search_on_site(query: str) -> str:
    """Find search input on current site and search."""
    driver = _get_driver()
    search_selectors = [
        "input[type='search']", "input[name='q']", "input[name='query']",
        "input[name='search']", "input[placeholder*='earch']",
        "input[aria-label*='earch']", "#search", ".search-input",
    ]
    for sel in search_selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            el.clear()
            el.send_keys(query)
            el.send_keys(Keys.RETURN)
            return f"Searched '{query}' on {driver.current_url}"
        except Exception:
            continue
    return "Could not find search box on this page"


# ═══════════════════════════════════════════════════════════
# TABS & NAVIGATION
# ═══════════════════════════════════════════════════════════

def new_tab(url: str = "") -> str:
    """Open a new tab, optionally navigate to URL."""
    driver = _get_driver()
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    if url:
        if not url.startswith("http"):
            url = "https://" + url
        driver.get(url)
        return f"New tab: {url}"
    return "Opened new tab"


def close_tab() -> str:
    """Close current tab."""
    driver = _get_driver()
    if len(driver.window_handles) > 1:
        driver.close()
        driver.switch_to.window(driver.window_handles[-1])
        return "Tab closed"
    return "Only one tab open"


def switch_tab(index: int = -1) -> str:
    """Switch to tab by index (-1 = last)."""
    driver = _get_driver()
    handles = driver.window_handles
    if not handles:
        return "No tabs"
    driver.switch_to.window(handles[index])
    return f"Switched to tab: {driver.title}"


def back() -> str:
    driver = _get_driver()
    driver.back()
    return f"Back → {driver.title}"


def forward() -> str:
    driver = _get_driver()
    driver.forward()
    return f"Forward → {driver.title}"


# ═══════════════════════════════════════════════════════════
# DATA EXTRACTION
# ═══════════════════════════════════════════════════════════

def get_weather(city: str = "") -> str:
    """Get weather from Google."""
    query = f"weather {city}" if city else "weather"
    driver = _get_driver()
    driver.get(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
    time.sleep(1.5)
    try:
        temp = driver.find_element(By.ID, "wob_tm").text
        desc = driver.find_element(By.ID, "wob_dc").text
        loc = driver.find_element(By.ID, "wob_loc").text
        return f"{loc}: {temp}°C, {desc}"
    except Exception:
        return read_page()[:500]


def get_news(topic: str = "") -> str:
    """Get headlines from Google News."""
    query = topic or "news today"
    driver = _get_driver()
    driver.get(f"https://news.google.com/search?q={urllib.parse.quote(query)}")
    time.sleep(2)
    try:
        articles = driver.find_elements(By.CSS_SELECTOR, "article h3, article h4")[:7]
        headlines = [a.text.strip() for a in articles if a.text.strip()]
        return "Headlines: " + " | ".join(headlines) if headlines else "Could not fetch headlines"
    except Exception:
        return read_page()[:500]


def screenshot(path: str = None) -> str:
    """Take a browser screenshot."""
    import os
    driver = _get_driver()
    path = path or os.path.join(os.path.expanduser("~"), "Desktop", "browser_screenshot.png")
    driver.save_screenshot(path)
    return f"Browser screenshot saved: {path}"


# ═══════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════

def close_browser() -> str:
    """Close the Selenium-controlled browser entirely."""
    global _driver
    if _driver:
        _driver.quit()
        _driver = None
        return "Browser closed"
    return "No browser was open"
