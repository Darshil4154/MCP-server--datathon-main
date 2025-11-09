"""Monday.com API client for fetching boards, items, and updates."""

import os
import sys
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class MondayClient:
    """Client for interacting with Monday.com API."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the Monday.com client.
        
        Args:
            token: Monday.com API token (defaults to MONDAY_API_TOKEN env var)
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests package not installed. Install it with: pip install requests"
            )
        
        self.token = token or os.getenv("MONDAY_API_TOKEN")
        if not self.token:
            raise ValueError(
                "MONDAY_API_TOKEN not found. Please set it in your .env file or pass it as a parameter."
            )
        
        self.base_url = "https://api.monday.com/v2"
        # Monday.com API v2 requires the token in the Authorization header
        # The token should be sent directly (not as "Bearer token")
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "API-Version": "2024-01"
        }
    
    def _make_request(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Make a GraphQL request to Monday.com API."""
        payload = {
            "query": query
        }
        if variables:
            payload["variables"] = variables
        
        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            # Check for HTTP errors
            if response.status_code == 401:
                raise RuntimeError(
                    "Monday.com API authorization failed (401). "
                    "Please check that your MONDAY_API_TOKEN is valid and not expired. "
                    "Get a new token from: https://monday.com/mypage/settings/api"
                )
            elif response.status_code == 403:
                raise RuntimeError(
                    "Monday.com API access forbidden (403). "
                    "Your token may not have the required permissions."
                )
            
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                error_msg = "; ".join([err.get("message", str(err)) for err in data["errors"]])
                raise RuntimeError(f"Monday.com API error: {error_msg}")
            
            return data.get("data", {})
        except requests.exceptions.RequestException as e:
            if "401" in str(e):
                raise RuntimeError(
                    "Monday.com API authorization failed. "
                    "Please verify your MONDAY_API_TOKEN is correct and active."
                )
            raise RuntimeError(f"Monday.com API request failed: {str(e)}")
    
    def get_boards(self, limit: int = 50) -> List[Dict]:
        """
        Get all boards.
        
        Args:
            limit: Maximum number of boards to return
        
        Returns:
            List of board dictionaries
        """
        query = """
        query GetBoards($limit: Int) {
            boards(limit: $limit) {
                id
                name
                description
                state
                board_kind
                items_count
                groups {
                    id
                    title
                }
            }
        }
        """
        
        variables = {"limit": limit}
        result = self._make_request(query, variables)
        return result.get("boards", [])
    
    def get_board_items(self, board_id: int, limit: int = 50) -> List[Dict]:
        """
        Get items from a specific board.
        
        Args:
            board_id: ID of the board
            limit: Maximum number of items to return
        
        Returns:
            List of item dictionaries
        """
        query = """
        query GetBoardItems($boardId: [Int!]!, $limit: Int) {
            boards(ids: $boardId, limit: $limit) {
                id
                name
                items_page(limit: $limit) {
                    items {
                        id
                        name
                        state
                        column_values {
                            id
                            text
                            value
                            type
                        }
                        updates(limit: 5) {
                            id
                            body
                            created_at
                            creator {
                                name
                                email
                            }
                        }
                        creator {
                            name
                            email
                        }
                        created_at
                    }
                }
            }
        }
        """
        
        variables = {"boardId": [board_id], "limit": limit}
        result = self._make_request(query, variables)
        boards = result.get("boards", [])
        if boards:
            items_page = boards[0].get("items_page", {})
            return items_page.get("items", [])
        return []
    
    def get_my_boards(self, limit: int = 50) -> List[Dict]:
        """
        Get boards that the current user has access to.
        
        Args:
            limit: Maximum number of boards to return
        
        Returns:
            List of board dictionaries
        """
        return self.get_boards(limit)
    
    def search_items(self, board_ids: List[int], query: str, limit: int = 20) -> List[Dict]:
        """
        Search for items across boards.
        
        Args:
            board_ids: List of board IDs to search in
            query: Search query string
            limit: Maximum number of results
        
        Returns:
            List of matching items
        """
        # Monday.com doesn't have a direct search API, so we'll get items from boards
        all_items = []
        for board_id in board_ids[:5]:  # Limit to 5 boards
            try:
                items = self.get_board_items(board_id, limit=limit)
                # Filter items by name containing query
                matching = [item for item in items if query.lower() in item.get("name", "").lower()]
                all_items.extend(matching)
            except:
                continue
        
        return all_items[:limit]
    
    def get_updates(self, item_id: int, limit: int = 10) -> List[Dict]:
        """
        Get updates for a specific item.
        
        Args:
            item_id: ID of the item
            limit: Maximum number of updates to return
        
        Returns:
            List of update dictionaries
        """
        query = """
        query GetItemUpdates($itemId: [Int!]!, $limit: Int) {
            items(ids: $itemId) {
                id
                name
                updates(limit: $limit) {
                    id
                    body
                    created_at
                    creator {
                        name
                        email
                    }
                }
            }
        }
        """
        
        variables = {"itemId": [item_id], "limit": limit}
        result = self._make_request(query, variables)
        items = result.get("items", [])
        if items:
            return items[0].get("updates", [])
        return []
    
    def get_workspaces(self) -> List[Dict]:
        """
        Get all workspaces.
        
        Returns:
            List of workspace dictionaries
        """
        query = """
        query GetWorkspaces {
            workspaces {
                id
                name
                kind
                description
            }
        }
        """
        
        result = self._make_request(query)
        return result.get("workspaces", [])

