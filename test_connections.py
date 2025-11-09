#!/usr/bin/env python3
"""Test both Calendar and GitHub connections."""
import sys
import os
sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv()

print("=" * 70)
print("Testing Connections")
print("=" * 70)

# Test GitHub
print("\n[1/2] Testing GitHub connection...")
try:
    from github_client import GitHubClient
    github_client = GitHubClient()
    user_info = github_client._make_request('/user')
    print(f"[OK] GitHub: Connected as {user_info.get('login', 'Unknown')}")
    github_ok = True
except Exception as e:
    print(f"[FAIL] GitHub: Failed - {str(e)}")
    github_ok = False

# Test Calendar
print("\n[2/2] Testing Calendar connection...")
try:
    from calendar_client import CalendarClient
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "config/credentials.json")
    token_path = os.getenv("GOOGLE_TOKEN_PATH", "config/token.json")
    
    if not os.path.exists(token_path):
        print("[FAIL] Calendar: No token file found. Run authenticate_calendar.py first.")
        calendar_ok = False
    else:
        calendar_client = CalendarClient(credentials_path, token_path)
        # Test by getting calendar timezone
        calendar = calendar_client.service.calendars().get(calendarId='primary').execute()
        timezone = calendar.get('timeZone', 'UTC')
        print(f"[OK] Calendar: Connected (Timezone: {timezone})")
        calendar_ok = True
except Exception as e:
    print(f"[FAIL] Calendar: Failed - {str(e)}")
    calendar_ok = False

# Summary
print("\n" + "=" * 70)
print("Summary")
print("=" * 70)
print(f"GitHub:  {'[OK] Connected' if github_ok else '[FAIL] Not Connected'}")
print(f"Calendar: {'[OK] Connected' if calendar_ok else '[FAIL] Not Connected'}")
print("=" * 70)

if not calendar_ok:
    print("\nTo authenticate Calendar, run: python authenticate_calendar.py")

