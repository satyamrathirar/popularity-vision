import time
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError

def fetch_google_trends(
    keywords=["n8n slack", "n8n google sheets", "n8n openai", "n8n http request", "n8n webhook"], 
    countries=['US', 'IN']
):
    print("Fetching data from Google Trends...")
    workflows = []

    for keyword in keywords:
        for country in countries:
            # --- Start of retry logic ---
            retries = 3
            for attempt in range(retries):
                try:
                    pytrends = TrendReq(hl='en-US', tz=360)
                    pytrends.build_payload([keyword], cat=0, timeframe='today 3-m', geo=country)
                    interest_df = pytrends.interest_over_time()

                    if not interest_df.empty and keyword in interest_df.columns:
                        average_interest = round(interest_df[keyword].mean(), 2)
                        print(f"  -> Trend for '{keyword}' in {country}: Avg Interest = {average_interest}")

                        metrics = {"relative_search_interest": average_interest, "timeframe_days": 90}
                        
                        workflows.append({
                            "workflow_name": f"Trend: {keyword}",
                            "platform": "Google Trends",
                            "country": country,
                            "popularity_metrics": metrics,
                            "source_url": f"https://trends.google.com/trends/explore?q={keyword.replace(' ', '%20')}&geo={country}"
                        })
                    else:
                        print(f"  -> No data for '{keyword}' in {country}.")
                    
                    break # Success, exit the retry loop

                except ResponseError as e:
                    print(f"  -> WARN: Request for '{keyword}' failed with {e.response.status_code}. Attempt {attempt + 1} of {retries}.")
                    if e.response.status_code == 429:
                        wait_time = (attempt + 1) * 5  # Wait 5s, then 10s, then 15s
                        print(f"  -> Rate limited. Waiting for {wait_time} seconds before retrying...")
                        time.sleep(wait_time)
                    else:
                        break # Don't retry for other errors
                except Exception as e:
                    print(f"  -> ERROR: An unexpected error occurred for keyword '{keyword}'. Reason: {e}")
                    break
            # --- End of retry logic ---
            time.sleep(1) # Small delay between different keywords

    print(f"Found {len(workflows)} potential trends from Google.")
    return workflows