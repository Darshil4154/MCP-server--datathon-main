#!/usr/bin/env python3
"""Authenticate Google Calendar and generate token."""
import sys
import os
sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv()

from calendar_client import CalendarClient

print("=" * 70)
print("Google Calendar Authentication")
print("=" * 70)
print("\nThis will open a browser window for you to sign in with Google.")
print("IMPORTANT: Make sure you have added your email as a test user in Google Cloud Console.")
print("If you see 'Error 403: access_denied', you need to add your email first.")
print("\nStarting authentication in 2 seconds...")
import time
time.sleep(2)

try:
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "config/credentials.json")
    token_path = os.getenv("GOOGLE_TOKEN_PATH", "config/token.json")
    
    print(f"\nUsing credentials: {credentials_path}")
    print(f"Token will be saved to: {token_path}\n")
    
    client = CalendarClient(credentials_path, token_path)
    
    print("\n" + "=" * 70)
    print("SUCCESS! Calendar authentication completed!")
    print("=" * 70)
    print(f"\nToken saved to: {token_path}")
    print("You can now use Calendar features in the Streamlit app.\n")
    
except Exception as e:
    print(f"\nERROR: {str(e)}")
    print("\nCommon issues:")
    print("1. Make sure your email is added as a test user in Google Cloud Console")
    print("2. Check that redirect URIs are configured correctly")
    print("3. Verify credentials.json file is correct\n")
    import traceback
    traceback.print_exc()

