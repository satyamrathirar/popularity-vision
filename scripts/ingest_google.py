import time
from pytrends.request import TrendReq

def fetch_google_trends(
    keywords=["n8n slack", "n8n google sheets", "n8n openai", "n8n http request", "n8n webhook"], 
    countries=['US', 'IN']
):
    print("Fetching data from Google Trends...")
    pytrends = TrendReq(hl='en-US', tz=360)
    workflows = []

    for keyword in keywords:
        for country in countries:
            try:
                # Build the payload for the last 90 days
                pytrends.build_payload([keyword], cat=0, timeframe='today 3-m', geo=country)
                
                # Fetch interest over time
                interest_df = pytrends.interest_over_time()

                if not interest_df.empty and keyword in interest_df.columns:
                    # Calculate average interest score (0-100 scale)
                    average_interest = round(interest_df[keyword].mean(), 2)
                    
                    print(f"  -> Trend for '{keyword}' in {country}: Avg Interest = {average_interest}")

                    metrics = {
                        "relative_search_interest": average_interest,
                        "timeframe_days": 90
                    }
                    
                    workflows.append({
                        "workflow_name": f"Trend: {keyword}",
                        "platform": "Google Trends",
                        "country": country,
                        "popularity_metrics": metrics,
                        "source_url": f"https://trends.google.com/trends/explore?q={keyword.replace(' ', '%20')}&geo={country}"
                    })
                else:
                    print(f"  -> No data for '{keyword}' in {country}.")

                # Be respectful to the API to avoid rate limiting
                time.sleep(1)

            except Exception as e:
                print(f"  -> ERROR: An error occurred for keyword '{keyword}' in {country}. Reason: {e}")

    print(f"Found {len(workflows)} potential trends from Google.")
    return workflows