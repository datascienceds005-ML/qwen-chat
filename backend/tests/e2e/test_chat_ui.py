import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


def test_load_hero_and_health_dot(server_url, page):
    page.goto(server_url)
    expect(page.locator(".hero")).to_be_visible()
    expect(page.locator("#statusDot.ok")).to_be_visible(timeout=10000)


def test_send_and_streamed_reply(server_url, page):
    page.goto(server_url)
    page.fill("#input", "Ping")
    page.click("#sendBtn")
    expect(page.locator(".msg.assistant").last).to_contain_text(
        "You said: Ping", timeout=15000
    )


def test_markdown_codeblock(server_url, page):
    page.goto(server_url)
    page.fill("#input", "write code")
    page.click("#sendBtn")
    expect(page.locator(".codeblock")).to_be_visible(timeout=15000)
    expect(page.locator(".codeblock code")).to_contain_text("def greet")


def test_stop_button_aborts(server_url, page):
    page.goto(server_url)
    page.fill("#input", "tell a long story")
    page.click("#sendBtn")
    expect(page.locator("#sendBtn")).to_have_text("■", timeout=5000)
    page.click("#sendBtn")
    expect(page.locator("#sendBtn")).to_have_text("↑", timeout=10000)


def test_history_persists_across_reload(server_url, page):
    page.goto(server_url)
    page.fill("#input", "Remember me")
    page.click("#sendBtn")
    expect(page.locator(".msg.assistant").last).to_contain_text("Remember me", timeout=15000)
    page.reload()
    expect(page.locator(".msg.user").last).to_contain_text("Remember me")


def test_new_chat_resets(server_url, page):
    page.goto(server_url)
    page.fill("#input", "Ping")
    page.click("#sendBtn")
    expect(page.locator(".msg.assistant").last).to_contain_text("You said", timeout=15000)
    page.click("#newChatBtn")
    expect(page.locator(".hero")).to_be_visible()
