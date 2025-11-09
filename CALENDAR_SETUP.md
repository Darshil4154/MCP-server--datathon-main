# Calendar Authentication Setup

## Step 1: Add Your Email as Test User (REQUIRED)

1. Go to: https://console.cloud.google.com/
2. Select your project: **gen-lang-client-0345738267**
3. Navigate to: **APIs & Services** → **OAuth consent screen**
4. Scroll down to the **"Test users"** section
5. Click **"ADD USERS"** button
6. Enter your email: **darshilrayjada4154@gmail.com**
7. Click **"ADD"**
8. Wait 1-2 minutes for changes to take effect

## Step 2: Authenticate Calendar

After adding your email, run:
```cmd
python authenticate_calendar.py
```

Or use the direct command:
```cmd
python -c "import sys; sys.path.insert(0, 'src'); from calendar_client import CalendarClient; CalendarClient('config/credentials.json', 'config/token.json')"
```

This will:
- Open a browser window
- Ask you to sign in with Google
- Create the token file automatically

## Step 3: Refresh Streamlit

After authentication:
1. Go to http://localhost:8501
2. Click "🔄 Refresh Data" button
3. Calendar should show as "✅ Connected"

