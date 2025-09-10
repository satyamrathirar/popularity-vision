from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import YOUTUBE_API_KEY
import os

def load_keywords_from_file(keywords_file="keywords.txt"):
    """Load keywords from an external file."""
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    keywords_path = os.path.join(script_dir, keywords_file)
    
    try:
        with open(keywords_path, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip()]
        return keywords
    except FileNotFoundError:
        print(f"Warning: Keywords file '{keywords_path}' not found. Using default keywords.")
        return ["n8n workflow", "n8n automation tutorial", "n8n slack"]

def fetch_youtube_workflows(keywords=None):
    if keywords is None:
        keywords = load_keywords_from_file()
    
    print("Fetching data from YouTube...")
    print(f"Using {len(keywords)} keywords from external file")
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
        print("ERROR: YouTube API Key is not configured in .env file.")
        return []

    workflows = []
    all_video_ids = []
    
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

        # 1. Search for videos with pagination - search one keyword at a time for deep pagination
        for keyword in keywords:
            print(f"  -> Searching for keyword: '{keyword}'")
            next_page_token = None
            pages_processed = 0
            max_pages = 5  # Limit to avoid quota exhaustion
            
            while pages_processed < max_pages:
                search_request = youtube.search().list(
                    q=keyword, # Now search one keyword at a time for deep pagination
                    part="snippet",
                    type="video",
                    maxResults=50, # Get max results per page
                    pageToken=next_page_token
                )
                search_response = search_request.execute()
                
                page_video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
                all_video_ids.extend(page_video_ids)
                
                pages_processed += 1
                print(f"    -> Page {pages_processed}: Found {len(page_video_ids)} videos")
                
                next_page_token = search_response.get('nextPageToken')
                if not next_page_token:
                    print(f"    -> No more pages for keyword '{keyword}'")
                    break # Exit the loop if this was the last page

        print(f"DEBUG: YouTube search found {len(all_video_ids)} total videos across all keywords and pages.")

        if not all_video_ids:
            return []

        # Remove duplicates while preserving order
        unique_video_ids = list(dict.fromkeys(all_video_ids))
        print(f"DEBUG: After removing duplicates: {len(unique_video_ids)} unique videos.")

        # 2. Get statistics for all found video IDs (process in batches due to API limits)
        batch_size = 50
        for i in range(0, len(unique_video_ids), batch_size):
            batch_ids = unique_video_ids[i:i + batch_size]
            
            video_request = youtube.videos().list(
                part="snippet,statistics",
                id=",".join(batch_ids)
            )
            video_response = video_request.execute()

            # 3. Process and format the data for this batch
            for item in video_response.get('items', []):
                stats = item.get('statistics', {})
                views = int(stats.get('viewCount', 0))
                likes = int(stats.get('likeCount', 0))
                comments = int(stats.get('commentCount', 0))
                
                if views == 0: continue # Skip videos with no views

                # Calculate engagement ratios
                like_to_view_ratio = round(likes / views, 6) if views > 0 else 0
                comment_to_view_ratio = round(comments / views, 6) if views > 0 else 0

                metrics = {
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "like_to_view_ratio": like_to_view_ratio,
                    "comment_to_view_ratio": comment_to_view_ratio,
                    "total_engagement": likes + comments,
                    "engagement_score": round((likes + comments) / views, 6) if views > 0 else 0
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