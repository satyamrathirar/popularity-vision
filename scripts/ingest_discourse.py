import requests
import time
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
        return ["workflow", "automation", "n8n"]

def fetch_discourse_workflows(keywords=None, max_keywords=None, max_pages_per_keyword=None):
    if keywords is None:
        keywords = load_keywords_from_file()
    
    # Limit keywords if specified
    if max_keywords and max_keywords < len(keywords):
        keywords = keywords[:max_keywords]
        print(f"Limited to first {max_keywords} keywords for testing")
    
    print("Fetching data from n8n Discourse forum...")
    print(f"Using {len(keywords)} keywords from external file")
    base_url = "https://community.n8n.io"
    workflows = []
    seen_urls = set()
 
    for keyword_index, keyword in enumerate(keywords, 1):
        print(f"[{keyword_index}/{len(keywords)}] -> Searching for keyword: '{keyword}'")
        page = 0
        # Use custom max_pages if provided, otherwise default to full collection
        max_pages = max_pages_per_keyword if max_pages_per_keyword else 10
        total_topics_for_keyword = 0
        
        try:
            while page < max_pages:
                search_url = f"{base_url}/search.json?q={keyword}&page={page}"
                search_res = requests.get(search_url, timeout=15)  # Add timeout for search requests
                search_res.raise_for_status()
                search_data = search_res.json()

                topics = search_data.get('topics', [])
                if not topics:
                    print(f"    -> Page {page}: No more topics found for keyword '{keyword}'")
                    break # Stop if a page has no topics
                
                print(f"    -> Page {page}: Found {len(topics)} topics for keyword '{keyword}'")
                total_topics_for_keyword += len(topics)

                for i, topic in enumerate(topics):
                    try:
                        topic_id = topic['id']
                        topic_url = f"{base_url}/t/{topic_id}.json"

                        if topic_url in seen_urls:
                            continue
                        seen_urls.add(topic_url)

                        print(f"      -> Processing topic {i+1}/{len(topics)}: '{topic['title']}' (ID: {topic_id})")

                        # Add timeout to prevent hanging
                        topic_res = requests.get(topic_url, timeout=10)
                        topic_res.raise_for_status()
                        topic_data = topic_res.json()

                        # Extract popularity signals
                        views = topic_data.get('views', 0)
                        replies = topic_data.get('reply_count', 0)
                        likes = topic_data.get('like_count', 0)
                        contributors = len(topic_data.get('details', {}).get('participants', []))
                        
                        # Skip topics with no engagement to speed up processing
                        if views == 0 and replies == 0 and likes == 0:
                            print(f"        -> Skipping topic with no engagement")
                            continue
                        
                        # Calculate engagement ratios (similar to YouTube)
                        reply_to_view_ratio = round(replies / views, 6) if views > 0 else 0
                        like_to_view_ratio = round(likes / views, 6) if views > 0 else 0
                        contributor_to_view_ratio = round(contributors / views, 6) if views > 0 else 0
                        
                        # Overall engagement score combining all interactions
                        total_engagement = replies + likes + contributors
                        engagement_score = round(total_engagement / views, 6) if views > 0 else 0

                        metrics = {
                            "views": views,
                            "replies": replies,
                            "likes": likes,
                            "contributors": contributors,
                            "reply_to_view_ratio": reply_to_view_ratio,
                            "like_to_view_ratio": like_to_view_ratio,
                            "contributor_to_view_ratio": contributor_to_view_ratio,
                            "total_engagement": total_engagement,
                            "engagement_score": engagement_score,
                            "replies_per_contributor": round(replies / contributors, 2) if contributors > 0 else 0
                        }
                        
                        workflows.append({
                            "workflow_name": topic_data['title'],
                            "platform": "Discourse",
                            "country": "Global",
                            "popularity_metrics": metrics,
                            "source_url": f"{base_url}/t/{topic_id}"
                        })
                        
                        # Reduce delay since we added timeout
                        time.sleep(0.05)  # Reduced from 0.1

                    except requests.exceptions.Timeout:
                        print(f"      -> TIMEOUT: Topic ID {topic_id} took too long to respond, skipping...")
                    except requests.exceptions.RequestException as e:
                        print(f"      -> WARN: Could not fetch details for topic ID {topic_id}. Reason: {e}")
                    except KeyError as e:
                        print(f"      -> WARN: Could not parse details for topic ID {topic_id}. Missing key: {e}")
                    except Exception as e:
                        print(f"      -> ERROR: Unexpected error for topic ID {topic_id}: {e}")
                
                page += 1
                # Reduce page delay since we're being more efficient
                time.sleep(0.2)  # Reduced from 0.5
            
            print(f"  -> Completed '{keyword}': {total_topics_for_keyword} topics processed, {len([w for w in workflows if keyword.lower() in w['workflow_name'].lower()])} workflows added")

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Could not perform search for keyword '{keyword}'. Reason: {e}")

    print(f"Found {len(workflows)} potential workflows from Discourse.")
    return workflows