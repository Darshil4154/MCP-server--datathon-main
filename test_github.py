#!/usr/bin/env python3
"""Test GitHub client initialization."""
import sys
import os
sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv()

from github_client import GitHubClient

try:
    token = os.getenv('GITHUB_TOKEN')
    print(f"Token found: {bool(token)}")
    print(f"Token length: {len(token) if token else 0}")
    
    client = GitHubClient()
    print("SUCCESS: GitHub client initialized")
    print(f"Base URL: {client.base_url}")
    
    # Test a simple API call
    response = client._make_request('/user')
    print(f"GitHub username: {response.get('login', 'Unknown')}")
    print("GitHub connection working!")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

