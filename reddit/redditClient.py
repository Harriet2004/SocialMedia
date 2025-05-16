# COSC2671 Social Media and Network Analytics
# Reddit API Client Setup using PRAW

import sys
import praw
import os
from dotenv import load_dotenv

def get_reddit_client():
    """
    Sets up and returns a PRAW Reddit client using credentials from a .env file.
    """

    # Load environment variables from .env
    load_dotenv()

    try:
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            username=os.getenv("REDDIT_USERNAME"),
            password=os.getenv("REDDIT_PASSWORD"),
            user_agent=os.getenv("REDDIT_USER_AGENT")
        )

        # Optional: validate connection
        reddit.user.me()  
        print(f"Connected to Reddit as: {user}")

    except Exception as e:
        sys.stderr.write(f"Reddit authentication failed: {e}\n")
        sys.exit(1)

    return reddit
