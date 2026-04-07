import pytest
from playwright.sync_api import Page, expect

def start_app_and_wait(page: Page):
    page.set_viewport_size({"width": 1280, "height": 1000})
    page.goto("http://localhost:8501")
    expect(page.get_by_text("🛡️ Guardian Sentinel")).to_be_visible(timeout=20000)

def test_app_loads(page: Page):
    start_app_and_wait(page)
    expect(page.get_by_role("button", name="🔄 Sync Live Inbox")).to_be_visible()

def test_sync_and_safe_inbox(page: Page):
    start_app_and_wait(page)
    page.get_by_role("button", name="🔄 Sync Live Inbox").click()
    
    # Use exact match for the metric value to avoid toast conflicts
    expect(page.get_by_text("2", exact=True)).to_be_visible(timeout=15000)
    
    # Safe Email
    expect(page.locator("button").filter(has_text="Quarterly Update Meeting")).to_be_visible(timeout=10000)
    page.locator("button").filter(has_text="Quarterly Update Meeting").click()
    
    expect(page.get_by_text("Team, please find the quarterly results")).to_be_visible()

def test_quarantine_and_explainable_ai(page: Page):
    start_app_and_wait(page)
    page.get_by_role("button", name="🔄 Sync Live Inbox").click()
    expect(page.get_by_text("2", exact=True)).to_be_visible(timeout=15000)
    
    # Navigate to Quarantine
    page.get_by_text("🛡️ Quarantine").click()
    expect(page.get_by_role("heading", name="🛡️ Quarantine")).to_be_visible(timeout=10000)
    
    # Find Threat
    threat_btn = page.locator("button").filter(has_text="URGENT")
    expect(threat_btn).to_be_visible(timeout=10000)
    threat_btn.click()
    
    # Assert XAI
    expect(page.get_by_text("🚨 BEC ATTACK DETECTED")).to_be_visible()

def test_kill_switch(page: Page):
    start_app_and_wait(page)
    page.get_by_role("button", name="🔄 Sync Live Inbox").click()
    expect(page.get_by_text("2", exact=True)).to_be_visible(timeout=15000)
    
    page.get_by_text("🛡️ Quarantine").click()
    
    # Select Threat
    page.locator("button").filter(has_text="URGENT").click()
    
    # Kill switch
    kill_btn = page.get_by_role("button", name="🗑️ Confirm Threat & Delete from Gmail")
    expect(kill_btn).to_be_visible()
    kill_btn.click()
    
    # Verify success
    expect(page.get_by_text("Neutralized: Threat moved to Gmail Trash.")).to_be_visible()
    expect(page.locator("button").filter(has_text="URGENT")).not_to_be_visible()
