#!/usr/bin/env python3
"""Test Monday.com API connection."""
import sys
import os
sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv()

from monday_client import MondayClient

try:
    token = os.getenv('MONDAY_API_TOKEN')
    print(f"Token found: {bool(token)}")
    print(f"Token length: {len(token) if token else 0}")
    print(f"Token starts with: {token[:30] if token else 'None'}...")
    
    client = MondayClient()
    print("\nTesting Monday.com API...")
    
    # Test simple query
    boards = client.get_boards(limit=5)
    print(f"\nSUCCESS! Found {len(boards)} boards:")
    for i, board in enumerate(boards, 1):
        print(f"  {i}. {board.get('name', 'Unnamed')} (ID: {board.get('id')})")
        print(f"     Items: {board.get('items_count', 0)}")
    
except Exception as e:
    print(f"\nERROR: {str(e)}")
    import traceback
    traceback.print_exc()

