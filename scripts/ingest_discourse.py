import requests
import time

def fetch_discourse_workflows(keywords=["workflow", "automation", "google sheets", "slack"]):
    print("Fetching data from n8n Discourse forum...")
    base_url = "https://community.n8n.io"
    workflows = []
    seen_urls = set()

    for keyword in keywords:
        try:
            search_url = f"{base_url}/search.json?q={keyword}"
            search_res = requests.get(search_url)
            search_res.raise_for_status()
            search_data = search_res.json()

            topics = search_data.get('topics', [])[:10] 
            
            print(f"DEBUG: Found {len(search_data.get('topics', []))} topics for keyword '{keyword}'. Processing a max of 10...")

            for i, topic in enumerate(topics):
                try:
                    topic_id = topic['id']
                    topic_url = f"{base_url}/t/{topic_id}.json"

                    if topic_url in seen_urls:
                        continue
                    seen_urls.add(topic_url)

                    print(f"  -> Processing topic {i+1}/{len(topics)}: '{topic['title']}' (ID: {topic_id})")

                    topic_res = requests.get(topic_url)
                    topic_res.raise_for_status()
                    topic_data = topic_res.json()

                    metrics = {
                        "views": topic_data.get('views', 0),
                        "replies": topic_data.get('reply_count', 0),
                        "likes": topic_data.get('like_count', 0),
                        "contributors": len(topic_data.get('details', {}).get('participants', []))
                    }
                    
                    workflows.append({
                        "workflow_name": topic_data['title'],
                        "platform": "Discourse",
                        "country": "Global",
                        "popularity_metrics": metrics,
                        "source_url": f"{base_url}/t/{topic_id}"
                    })
                    
                    time.sleep(0.1) 

                except requests.exceptions.RequestException as e:
                    print(f"  -> WARN: Could not fetch details for topic ID {topic_id}. Reason: {e}")
                except KeyError as e:
                    print(f"  -> WARN: Could not parse details for topic ID {topic_id}. Missing key: {e}")

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Could not perform search for keyword '{keyword}'. Reason: {e}")

    print(f"Found {len(workflows)} potential workflows from Discourse.")
    return workflows