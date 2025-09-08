from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import YOUTUBE_API_KEY

def fetch_youtube_workflows(keywords=["n8n workflow", "n8n automation tutorial", "n8n slack"]):
    print("Fetching data from YouTube...")
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
        print("ERROR: YouTube API Key is not configured in .env file.")
        return []

    workflows = []
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

        # 1. Search for videos
        search_request = youtube.search().list(
            q="|".join(keywords), # Use OR logic for keywords
            part="snippet",
            type="video",
            maxResults=25 # Get a decent number of results
        )
        search_response = search_request.execute()
        print(f"DEBUG: YouTube search found {len(search_response.get('items', []))} initial videos.")

        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

        if not video_ids:
            return []

        # 2. Get statistics for all found video IDs in one call
        video_request = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(video_ids)
        )
        video_response = video_request.execute()

        # 3. Process and format the data
        for item in video_response.get('items', []):
            stats = item.get('statistics', {})
            views = int(stats.get('viewCount', 0))
            likes = int(stats.get('likeCount', 0))
            
            if views == 0: continue # Skip videos with no views

            metrics = {
                "views": views,
                "likes": likes,
                "comments": int(stats.get('commentCount', 0)),
                "like_to_view_ratio": round(likes / views, 4) if views > 0 else 0,
            }
            
            workflows.append({
                "workflow_name": item['snippet']['title'],
                "platform": "YouTube",
                "country": "Global", # YouTube data is global by default
                "popularity_metrics": metrics,
                "source_url": f"https://www.youtube.com/watch?v={item['id']}"
            })

    except HttpError as e:
        print(f"ERROR: An HTTP error {e.resp.status} occurred: {e.content}")
    
    print(f"Found {len(workflows)} potential workflows from YouTube.")
    return workflows