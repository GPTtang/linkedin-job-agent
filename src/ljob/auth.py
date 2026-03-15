import shutil
from playwright.sync_api import sync_playwright
from .config import BROWSER_PROFILE_DIR


def login_linkedin() -> None:
    BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_PROFILE_DIR),
            headless=False,
        )
        page = context.new_page()
        page.goto("https://www.linkedin.com/login")
        print("请在浏览器中手动登录 LinkedIn，完成后回终端按 Enter。")
        input()
        context.close()


def auth_status() -> bool:
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_PROFILE_DIR),
            headless=False,
        )
        page = context.new_page()
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        ok = "feed" in page.url or "linkedin.com/in/" in page.url
        context.close()
        return ok


def logout_linkedin() -> None:
    if BROWSER_PROFILE_DIR.exists():
        shutil.rmtree(BROWSER_PROFILE_DIR)
