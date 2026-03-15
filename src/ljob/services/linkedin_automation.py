"""
Playwright automation for updating LinkedIn profile.

Opens browser in non-headless mode (user can see everything).
Best-effort automation — falls back gracefully if LinkedIn's UI changes.
"""
import time
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..config import BROWSER_PROFILE_DIR

_PROFILE_URL = "https://www.linkedin.com/in/me/"
_RESUME_SETTINGS_URL = "https://www.linkedin.com/jobs/application-settings/"
_SLOW_MO = 400  # ms between actions — helps avoid detection and improves stability


def _launch(p):
    return p.chromium.launch_persistent_context(
        user_data_dir=str(BROWSER_PROFILE_DIR),
        headless=False,
        slow_mo=_SLOW_MO,
    )


def _is_logged_in(page) -> bool:
    return "login" not in page.url and "authwall" not in page.url


def _try_click(page, selectors: list[str], timeout: int = 4000) -> bool:
    """Try each selector in order, click first one found. Returns True if clicked."""
    for sel in selectors:
        try:
            el = page.locator(sel).first
            el.wait_for(state="visible", timeout=timeout)
            el.click()
            return True
        except Exception:
            continue
    return False


def _try_fill(page, selectors: list[str], value: str, timeout: int = 4000) -> bool:
    """Try each selector in order, fill first one found. Returns True if filled."""
    for sel in selectors:
        try:
            el = page.locator(sel).first
            el.wait_for(state="visible", timeout=timeout)
            el.triple_click()
            el.fill(value)
            return True
        except Exception:
            continue
    return False


def update_linkedin_profile(headline: str, about: str) -> dict:
    """
    Update LinkedIn headline and About section.

    Returns:
        {
          "headline_updated": bool,
          "about_updated": bool,
          "errors": list[str],
        }
    """
    result = {"headline_updated": False, "about_updated": False, "errors": []}

    with sync_playwright() as p:
        context = _launch(p)
        page = context.new_page()

        try:
            page.goto(_PROFILE_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)

            if not _is_logged_in(page):
                result["errors"].append("未登录 LinkedIn，请先运行：python main.py auth login")
                return result

            # ── Update Headline ──────────────────────────────────────────────
            # Click the "Edit intro" pencil button
            clicked = _try_click(page, [
                "button[aria-label='Edit intro']",
                "button[aria-label*='Edit intro']",
                "a[data-control-name='edit_intro']",
            ])

            if clicked:
                time.sleep(1)
                filled = _try_fill(page, [
                    "input#headline",
                    "input[id*='headline']",
                    "input[name='headline']",
                ], headline[:120])

                if filled:
                    # Click Save button in the modal
                    saved = _try_click(page, [
                        "button[aria-label='Save']",
                        "div[data-view-name*='profile-edit'] button.artdeco-button--primary",
                        "button.artdeco-button--primary",
                    ])
                    if saved:
                        time.sleep(2)
                        result["headline_updated"] = True
                    else:
                        result["errors"].append("找到 Headline 输入框但无法点击保存按钮")
                else:
                    result["errors"].append("打开了编辑弹窗但未找到 Headline 输入框")
                    # Close modal
                    _try_click(page, ["button[aria-label='Dismiss']", "button.artdeco-modal__dismiss"])
            else:
                result["errors"].append("未找到 'Edit intro' 按钮，请确认已登录且在个人主页")

            time.sleep(1)

            # ── Update About ─────────────────────────────────────────────────
            if about:
                # Scroll to About section and click its edit button
                try:
                    page.evaluate("window.scrollTo(0, 400)")
                    time.sleep(1)
                except Exception:
                    pass

                clicked_about = _try_click(page, [
                    "section#about-section button[aria-label*='Edit']",
                    "section:has(#about) button[aria-label*='Edit']",
                    "button[aria-label*='Edit about']",
                    "#about ~ div button[aria-label*='Edit']",
                ])

                if clicked_about:
                    time.sleep(1)
                    filled_about = _try_fill(page, [
                        "textarea#summary",
                        "textarea[id*='summary']",
                        "textarea[name='summary']",
                        "div[data-placeholder*='summary'] div[contenteditable]",
                    ], about[:2600])

                    if filled_about:
                        saved_about = _try_click(page, [
                            "button[aria-label='Save']",
                            "div[data-view-name*='profile-edit'] button.artdeco-button--primary",
                            "button.artdeco-button--primary",
                        ])
                        if saved_about:
                            time.sleep(2)
                            result["about_updated"] = True
                        else:
                            result["errors"].append("找到 About 输入框但无法点击保存按钮")
                    else:
                        result["errors"].append("打开了 About 编辑弹窗但未找到文本框")
                        _try_click(page, ["button[aria-label='Dismiss']", "button.artdeco-modal__dismiss"])
                else:
                    result["errors"].append("未找到 About 编辑按钮（About 区块可能还未添加）")

        except PlaywrightTimeout as e:
            result["errors"].append(f"页面超时：{str(e)[:80]}")
        except Exception as e:
            result["errors"].append(f"自动化错误：{str(e)[:120]}")
        finally:
            time.sleep(1)
            context.close()

    return result


def upload_linkedin_resume(file_path: str) -> dict:
    """
    Upload a resume PDF to LinkedIn's Easy Apply resume storage.
    Navigates to: linkedin.com/jobs/application-settings/

    Returns:
        {
          "uploaded": bool,
          "errors": list[str],
        }
    """
    result = {"uploaded": False, "errors": []}

    if not Path(file_path).exists():
        result["errors"].append(f"文件不存在：{file_path}")
        return result

    suffix = Path(file_path).suffix.lower()
    if suffix not in (".pdf", ".doc", ".docx"):
        result["errors"].append(f"不支持的文件类型：{suffix}（支持 .pdf / .doc / .docx）")
        return result

    with sync_playwright() as p:
        context = _launch(p)
        page = context.new_page()

        try:
            page.goto(_RESUME_SETTINGS_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)

            if not _is_logged_in(page):
                result["errors"].append("未登录 LinkedIn，请先运行：python main.py auth login")
                return result

            # LinkedIn's resume upload input is a hidden file input
            # Trigger it via label or direct set_input_files
            file_input = page.locator("input[type='file']").first
            file_input.set_input_files(file_path)
            time.sleep(3)

            # Confirm upload if there's a confirm button
            _try_click(page, [
                "button[aria-label*='Upload']",
                "button:has-text('Upload')",
                "button:has-text('Save')",
            ], timeout=3000)
            time.sleep(2)

            result["uploaded"] = True

        except PlaywrightTimeout as e:
            result["errors"].append(f"页面超时：{str(e)[:80]}")
        except Exception as e:
            result["errors"].append(f"上传失败：{str(e)[:120]}")
        finally:
            context.close()

    return result
