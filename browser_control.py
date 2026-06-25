"""
Isabella - browser control.

Full browser automation: open sites, search, play YouTube/Spotify.
Uses os.startfile for reliable URL opening on Windows.
"""
import os
import subprocess
import time
import urllib.parse

import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3


def _wait(sec=1.5):
    time.sleep(sec)


def _focus_browser():
    """Bring browser to front."""
    try:
        subprocess.run(
            ["powershell", "-Command",
             "(New-Object -ComObject WScript.Shell).AppActivate('Chrome') -or "
             "(New-Object -ComObject WScript.Shell).AppActivate('Edge') -or "
             "(New-Object -ComObject WScript.Shell).AppActivate('Firefox')"],
            capture_output=True, timeout=3
        )
        _wait(0.5)
    except Exception:
        pass


def _open_url(url: str):
    """Reliably open a URL in default browser on Windows."""
    if not url.startswith("http"):
        url = "https://" + url
    os.startfile(url)


def open_and_search(url: str, query: str) -> str:
    """Open a website and search for something using direct URL."""
    try:
        if "youtube" in url:
            search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        elif "google" in url:
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        elif "spotify" in url:
            search_url = f"https://open.spotify.com/search/{urllib.parse.quote(query)}"
        else:
            search_url = f"{url}/search?q={urllib.parse.quote(query)}"
        _open_url(search_url)
        return f"Searched '{query}' on {url}"
    except Exception as e:
        return f"Failed: {e}"


def youtube_play(query: str) -> str:
    """Open YouTube and play the first video result."""
    try:
        # Use yt-dlp to get first video ID (most reliable)
        try:
            result = subprocess.run(
                ["yt-dlp", "--get-id", "--no-playlist", f"ytsearch1:{query}"],
                capture_output=True, text=True, timeout=20
            )
            if result.returncode == 0 and result.stdout.strip():
                video_id = result.stdout.strip().split('\n')[0]
                _open_url(f"https://www.youtube.com/watch?v={video_id}")
                return f"Playing '{query}' on YouTube"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Fallback: open search and click first result
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        _open_url(url)
        _wait(5)
        _focus_browser()
        _wait(1)
        for _ in range(6):
            pyautogui.press("tab")
            _wait(0.15)
        pyautogui.press("enter")
        return f"Playing '{query}' on YouTube"
    except Exception as e:
        return f"Failed: {e}"


def spotify_play(query: str) -> str:
    """Open Spotify web search directly."""
    try:
        url = f"https://open.spotify.com/search/{urllib.parse.quote(query)}"
        _open_url(url)
        _wait(3)
        _focus_browser()
        pyautogui.press("tab")
        _wait(0.3)
        pyautogui.press("enter")
        return f"Playing '{query}' on Spotify"
    except Exception as e:
        return f"Failed: {e}"


def browser_type(text: str) -> str:
    """Type text into whatever is currently focused."""
    try:
        _focus_browser()
        _wait(0.3)
        if text.isascii():
            pyautogui.typewrite(text, interval=0.03)
        else:
            subprocess.run(["powershell", "-Command", f"Set-Clipboard -Value '{text.replace(chr(39), chr(39)+chr(39))}'"],
                          capture_output=True, timeout=3)
            pyautogui.hotkey("ctrl", "v")
        return f"Typed: {text[:50]}"
    except Exception as e:
        return f"Failed: {e}"


def browser_address_bar(url: str) -> str:
    """Navigate to URL using address bar."""
    try:
        _focus_browser()
        pyautogui.hotkey("ctrl", "l")
        _wait(0.3)
        if not url.startswith("http"):
            url = "https://" + url
        pyautogui.typewrite(url, interval=0.02)
        pyautogui.press("enter")
        return f"Navigated to {url}"
    except Exception as e:
        return f"Failed: {e}"


def browser_back() -> str:
    try:
        _focus_browser()
        pyautogui.hotkey("alt", "left")
        return "Went back"
    except Exception as e:
        return f"Failed: {e}"


def browser_forward() -> str:
    try:
        _focus_browser()
        pyautogui.hotkey("alt", "right")
        return "Went forward"
    except Exception as e:
        return f"Failed: {e}"


def browser_refresh() -> str:
    try:
        _focus_browser()
        pyautogui.press("f5")
        return "Refreshed page"
    except Exception as e:
        return f"Failed: {e}"


def browser_scroll(direction: str = "down", amount: int = 5) -> str:
    try:
        _focus_browser()
        clicks = amount if direction == "up" else -amount
        pyautogui.scroll(clicks)
        return f"Scrolled {direction}"
    except Exception as e:
        return f"Failed: {e}"


def browser_fullscreen() -> str:
    try:
        _focus_browser()
        pyautogui.press("f11")
        return "Toggled fullscreen"
    except Exception as e:
        return f"Failed: {e}"


def google_search(query: str) -> str:
    try:
        _open_url(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
        return f"Googled: {query}"
    except Exception as e:
        return f"Failed: {e}"


def close_current_tab() -> str:
    try:
        _focus_browser()
        pyautogui.hotkey("ctrl", "w")
        return "Tab closed"
    except Exception as e:
        return f"Failed: {e}"


def new_tab(url: str = "") -> str:
    try:
        _focus_browser()
        pyautogui.hotkey("ctrl", "t")
        _wait(0.5)
        if url:
            pyautogui.typewrite(url if url.startswith("http") else "https://" + url, interval=0.02)
            pyautogui.press("enter")
            return f"New tab: {url}"
        return "Opened new tab"
    except Exception as e:
        return f"Failed: {e}"
