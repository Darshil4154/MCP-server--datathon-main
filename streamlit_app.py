#!/usr/bin/env python3
"""
Project Management Assistant Dashboard
A lightweight dashboard integrating GitHub and Google Calendar for project management.
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.server import chat
from src.calendar_client import CalendarClient
from src.github_client import GitHubClient
from src.monday_client import MondayClient
from src.query_analyzer import QueryAnalyzer

# Page configuration
st.set_page_config(
    page_title="Project Management Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .mcp-highlight {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .event-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #667eea;
    }
    .repo-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #28a745;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "calendar_client" not in st.session_state:
    st.session_state.calendar_client = None

if "github_client" not in st.session_state:
    st.session_state.github_client = None

if "monday_client" not in st.session_state:
    st.session_state.monday_client = None

def initialize_clients():
    """Initialize calendar and GitHub clients."""
    # Calendar - only if token exists
    try:
        if st.session_state.calendar_client is None:
            token_path = os.getenv("GOOGLE_TOKEN_PATH", "config/token.json")
            if os.path.exists(token_path):
                credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "config/credentials.json")
                import sys
                original_stdout = sys.stdout
                try:
                    sys.stdout = sys.stderr
                    st.session_state.calendar_client = CalendarClient(credentials_path, token_path)
                finally:
                    sys.stdout = original_stdout
    except:
        st.session_state.calendar_client = None
    
    # GitHub - ALWAYS try to initialize
    try:
        if st.session_state.github_client is None:
            # Load .env file directly
            env_file = os.path.join(os.path.dirname(__file__), '.env')
            load_dotenv(dotenv_path=env_file, override=True)
            
            github_token = os.getenv("GITHUB_TOKEN", "").strip()
            if github_token:
                st.session_state.github_client = GitHubClient(token=github_token)
                # Test it works
                try:
                    st.session_state.github_client._make_request('/user')
                except:
                    pass  # Keep client even if test fails
            else:
                st.session_state.github_client = None
    except Exception as e:
        st.session_state.github_client = None
    
    # Monday.com - ALWAYS try to initialize
    try:
        if st.session_state.monday_client is None:
            env_file = os.path.join(os.path.dirname(__file__), '.env')
            load_dotenv(dotenv_path=env_file, override=True)
            
            monday_token = os.getenv("MONDAY_API_TOKEN", "").strip()
            if monday_token:
                st.session_state.monday_client = MondayClient(token=monday_token)
    except Exception as e:
        st.session_state.monday_client = None

def format_time(dt_str):
    """Format datetime string for display."""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%I:%M %p')
    except:
        return dt_str

def format_date(dt_str):
    """Format date string for display."""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%b %d, %Y')
    except:
        return dt_str

def get_calendar_summary():
    """Get calendar summary for today and upcoming week."""
    if st.session_state.calendar_client is None:
        return [], []
    
    try:
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = today_start + timedelta(days=7)
        
        events = st.session_state.calendar_client.get_events_from_all_calendars(
            time_min=today_start,
            time_max=week_end,
            max_results=50
        )
        
        today_events = []
        upcoming_events = []
        
        for event in events:
            start = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
            if start:
                try:
                    event_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    event['parsed_start'] = event_dt
                    
                    if event_dt.date() == now.date():
                        today_events.append(event)
                    elif event_dt.date() > now.date():
                        upcoming_events.append(event)
                except:
                    pass
        
        # Sort events by time
        today_events.sort(key=lambda x: x.get('parsed_start', datetime.min))
        upcoming_events.sort(key=lambda x: x.get('parsed_start', datetime.min))
        
        return today_events, upcoming_events[:10]
    except Exception as e:
        return [], []

def get_github_summary():
    """Get GitHub activity summary."""
    if st.session_state.github_client is None:
        return None
    
    try:
        user_info = st.session_state.github_client.get_user_info()
        repos = st.session_state.github_client.get_repositories(per_page=10)
        
        # Get issues and PRs
        all_issues = []
        all_prs = []
        
        for repo in repos[:5]:
            owner = repo.get('owner', {}).get('login', user_info.get('login'))
            repo_name = repo.get('name', '')
            try:
                issues = st.session_state.github_client.get_issues(owner, repo_name, state='open', per_page=5)
                all_issues.extend(issues)
            except:
                pass
            
            try:
                prs = st.session_state.github_client.get_pull_requests(owner, repo_name, state='open', per_page=5)
                all_prs.extend(prs)
            except:
                pass
        
        return {
            'user_info': user_info,
            'repos': repos,
            'open_issues': all_issues[:10],
            'open_prs': all_prs[:10]
        }
    except Exception as e:
        return None

def main():
    # Header
    st.markdown('<h1 class="main-header">📊 Project Management <span class="mcp-highlight">MCP Server</span> Assistant</h1>', unsafe_allow_html=True)
    
    # Force reload .env file and clear session state if needed
    load_dotenv(override=True)
    
    # Clear clients if refresh button was clicked or on first load
    if "clients_initialized" not in st.session_state:
        st.session_state.calendar_client = None
        st.session_state.github_client = None
        st.session_state.clients_initialized = True
    
    # Initialize clients
    initialize_clients()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            # Clear all session state related to clients
            st.session_state.calendar_client = None
            st.session_state.github_client = None
            st.session_state.monday_client = None
            st.session_state.clients_initialized = False
            # Force reload .env
            load_dotenv(override=True)
            # Reinitialize
            initialize_clients()
            st.rerun()
        
        st.divider()
        
        # Status indicators
        st.subheader("🔌 Connections")
        
        # Debug info (can be removed later)
        github_token_check = os.getenv("GITHUB_TOKEN")
        st.caption(f"Token loaded: {'Yes' if github_token_check else 'No'}")
        
        calendar_status = "✅ Connected" if st.session_state.calendar_client else "❌ Not Connected"
        github_status = "✅ Connected" if st.session_state.github_client else "❌ Not Connected"
        monday_status = "✅ Connected" if st.session_state.monday_client else "❌ Not Connected"
        
        st.write(f"**Calendar:** {calendar_status}")
        st.write(f"**GitHub:** {github_status}")
        st.write(f"**Monday.com:** {monday_status}")
        
        # Show error if GitHub not connected but token exists
        if not st.session_state.github_client:
            if hasattr(st.session_state, 'github_error'):
                st.error(f"GitHub Error: {st.session_state.github_error}")
            elif github_token_check:
                st.warning("GitHub token found but client not initialized. Click Refresh Data.")
        
        if not st.session_state.calendar_client:
            st.info("💡 Configure Google Calendar credentials to enable calendar features.")
        if not st.session_state.github_client:
            st.info("💡 Set GITHUB_TOKEN in .env to enable GitHub features.")
        if not st.session_state.monday_client:
            st.info("💡 Set MONDAY_API_TOKEN in .env to enable Monday.com features.")
        
        st.divider()
        
        st.subheader("💬 AI Assistant")
        st.caption("Ask questions about your projects, schedule, or GitHub activity")
    
    # Main content - AI Assistant only
    st.header("💬 AI Assistant")
    st.caption("Ask me anything about your projects, schedule, or GitHub activity")
    
    # Predefined queries organized by category
    st.subheader("📋 Predefined Queries")
    
    # Calendar queries
    st.markdown("#### 📅 Calendar & Schedule")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📅 What's my schedule today?", use_container_width=True):
            st.session_state.quick_query = "What's my schedule today?"
            st.rerun()
        if st.button("📆 What meetings do I have this week?", use_container_width=True):
            st.session_state.quick_query = "What meetings do I have this week?"
            st.rerun()
        if st.button("⏰ When am I free tomorrow?", use_container_width=True):
            st.session_state.quick_query = "When am I free tomorrow?"
            st.rerun()
    
    with col2:
        if st.button("📋 Summarize my schedule for Monday", use_container_width=True):
            st.session_state.quick_query = "Summarize my schedule for Monday"
            st.rerun()
        if st.button("🔍 Am I free next week?", use_container_width=True):
            st.session_state.quick_query = "Am I free next week?"
            st.rerun()
        if st.button("📊 Show upcoming events", use_container_width=True):
            st.session_state.quick_query = "Show me my upcoming events"
            st.rerun()
    
    with col3:
        if st.button("⏳ Check availability at 2 PM", use_container_width=True):
            st.session_state.quick_query = "Am I available tomorrow at 2 PM?"
            st.rerun()
        if st.button("📅 What's on my calendar next week?", use_container_width=True):
            st.session_state.quick_query = "What's on my calendar next week?"
            st.rerun()
        if st.button("🔎 Detect scheduling conflicts", use_container_width=True):
            st.session_state.quick_query = "Are there any scheduling conflicts this week?"
            st.rerun()
    
    st.divider()
    
    # GitHub queries
    st.markdown("#### 🐙 GitHub & Repositories")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📦 Show my repositories", use_container_width=True):
            st.session_state.quick_query = "Show me my recent repositories"
            st.rerun()
        if st.button("🐛 What issues need attention?", use_container_width=True):
            st.session_state.quick_query = "What are my open issues?"
            st.rerun()
        if st.button("🔀 Show open pull requests", use_container_width=True):
            st.session_state.quick_query = "What PRs are open in my repos?"
            st.rerun()
    
    with col2:
        if st.button("🚀 Show current deployments", use_container_width=True):
            st.session_state.quick_query = "Show current deployments setup on GitHub"
            st.rerun()
        if st.button("📝 Recent commits", use_container_width=True):
            st.session_state.quick_query = "Show me my recent commits"
            st.rerun()
        if st.button("📊 GitHub activity summary", use_container_width=True):
            st.session_state.quick_query = "Give me a summary of my GitHub activity"
            st.rerun()
    
    with col3:
        if st.button("🔍 Search repositories", use_container_width=True):
            st.session_state.quick_query = "What repositories do I have?"
            st.rerun()
        if st.button("📈 Production deployments", use_container_width=True):
            st.session_state.quick_query = "What deployments are live in production?"
            st.rerun()
        if st.button("📚 Repository details", use_container_width=True):
            st.session_state.quick_query = "Tell me about my repositories"
            st.rerun()
    
    st.divider()
    
    # Custom query input
    st.subheader("💭 Custom Query")
    user_input = st.text_input("Enter your question:", placeholder="e.g., What meetings do I have today?")
    
    # Process user input
    if user_input:
        with st.spinner("Thinking..."):
            try:
                # Auto-detect GitHub and Monday.com queries
                message_lower = user_input.lower()
                include_github = any(keyword in message_lower for keyword in 
                                   ['github', 'repo', 'repository', 'issue', 'pr', 'pull request', 'commit',
                                    'deployment', 'deploy', 'deployed', 'deploying', 'production', 'staging'])
                include_monday = any(keyword in message_lower for keyword in 
                                   ['monday', 'project', 'timeline', 'board', 'task', 'item', 'sprint', 
                                    'milestone', 'deadline', 'status', 'progress', 'workflow'])
                
                response = chat(
                    message=user_input,
                    include_calendar_context=True,
                    include_github_context=include_github,
                    include_monday_context=include_monday
                )
                
                st.markdown("### Response:")
                st.write(response)
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
    
    # Handle quick query
    if hasattr(st.session_state, 'quick_query') and st.session_state.quick_query:
        query = st.session_state.quick_query
        del st.session_state.quick_query
        
        with st.spinner("Thinking..."):
            try:
                message_lower = query.lower()
                include_github = any(keyword in message_lower for keyword in 
                                   ['github', 'repo', 'repository', 'issue', 'pr', 'pull request', 'commit',
                                    'deployment', 'deploy', 'deployed', 'deploying', 'production', 'staging'])
                include_monday = any(keyword in message_lower for keyword in 
                                   ['monday', 'project', 'timeline', 'board', 'task', 'item', 'sprint', 
                                    'milestone', 'deadline', 'status', 'progress', 'workflow'])
                
                response = chat(
                    message=query,
                    include_calendar_context=True,
                    include_github_context=include_github,
                    include_monday_context=include_monday
                )
                
                st.markdown("### Response:")
                st.write(response)
            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
