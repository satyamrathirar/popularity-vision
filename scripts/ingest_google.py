import time
import os
import pandas as pd
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError

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
        return ["n8n slack", "n8n google sheets", "n8n openai", "n8n http request", "n8n webhook"]

def calculate_trend_direction(df, keyword, days=30):
    """Calculate if trend is going up or down over the specified days"""
    if df.empty or keyword not in df.columns:
        return {"trend_direction": "unknown", "change_percentage": 0}
    
    # Get the last 'days' worth of data
    recent_data = df[keyword].tail(min(days, len(df)))
    if len(recent_data) < 2:
        return {"trend_direction": "insufficient_data", "change_percentage": 0}
    
    # Calculate trend using linear regression slope
    x = list(range(len(recent_data)))
    y = recent_data.values
    
    # Simple slope calculation
    n = len(x)
    slope = (n * sum(x[i] * y[i] for i in range(n)) - sum(x) * sum(y)) / (n * sum(x[i]**2 for i in range(n)) - sum(x)**2)
    
    # Calculate percentage change from start to end of period
    start_value = recent_data.iloc[0] if recent_data.iloc[0] > 0 else 1
    end_value = recent_data.iloc[-1]
    change_percentage = round(((end_value - start_value) / start_value) * 100, 2)
    
    # Determine trend direction
    if slope > 0.1:
        trend_direction = "trending_up"
    elif slope < -0.1:
        trend_direction = "trending_down"
    else:
        trend_direction = "stable"
    
    return {
        "trend_direction": trend_direction,
        "change_percentage": change_percentage,
        "slope": round(slope, 4)
    }

def fetch_google_trends(
    keywords=None, 
    countries=['US', 'IN']
):
    if keywords is None:
        keywords = load_keywords_from_file()
    
    print("Fetching data from Google Trends...")
    print(f"Using {len(keywords)} keywords from external file")
    workflows = []

    for keyword in keywords:
        for country in countries:
            print(f"  -> Processing keyword: '{keyword}' in {country}")
            # --- Start of retry logic ---
            retries = 3
            for attempt in range(retries):
                try:
                    pytrends = TrendReq(hl='en-US', tz=360)
                    
                    # Get 12-month data for better trend analysis
                    pytrends.build_payload([keyword], cat=0, timeframe='today 12-m', geo=country)
                    interest_12m_df = pytrends.interest_over_time()
                    
                    # Get 3-month data for recent trends
                    pytrends.build_payload([keyword], cat=0, timeframe='today 3-m', geo=country)
                    interest_3m_df = pytrends.interest_over_time()
                    
                    # Get related queries for additional insights
                    try:
                        related_queries = pytrends.related_queries()
                        related_top = related_queries.get(keyword, {}).get('top', pd.DataFrame())
                        related_rising = related_queries.get(keyword, {}).get('rising', pd.DataFrame())
                    except:
                        related_top = pd.DataFrame()
                        related_rising = pd.DataFrame()

                    if not interest_12m_df.empty and keyword in interest_12m_df.columns:
                        # Calculate various metrics
                        current_interest = round(interest_3m_df[keyword].mean(), 2) if not interest_3m_df.empty else 0
                        annual_average = round(interest_12m_df[keyword].mean(), 2)
                        peak_interest = int(interest_12m_df[keyword].max())
                        recent_peak = int(interest_3m_df[keyword].max()) if not interest_3m_df.empty else 0
                        
                        # Calculate trend changes over different periods
                        trend_30d = calculate_trend_direction(interest_3m_df, keyword, 30)
                        trend_60d = calculate_trend_direction(interest_3m_df, keyword, 60)
                        trend_90d = calculate_trend_direction(interest_3m_df, keyword, 90)
                        
                        # Calculate momentum (recent vs historical average)
                        momentum_score = round((current_interest / annual_average) if annual_average > 0 else 0, 2)
                        
                        # Volatility (standard deviation as indicator of search consistency)
                        volatility = round(interest_12m_df[keyword].std(), 2)
                        
                        # Related query insights
                        related_query_count = len(related_top) + len(related_rising)
                        rising_queries_count = len(related_rising)

                        print(f"    -> Current Interest: {current_interest}, Annual Avg: {annual_average}, 30d Trend: {trend_30d['trend_direction']}")

                        metrics = {
                            # Core popularity signals
                            "relative_search_interest": current_interest,
                            "annual_average_interest": annual_average,
                            "peak_interest_12m": peak_interest,
                            "recent_peak_interest": recent_peak,
                            
                            # Trend analysis
                            "trend_30d": trend_30d,
                            "trend_60d": trend_60d,
                            "trend_90d": trend_90d,
                            
                            # Additional signals
                            "momentum_score": momentum_score,
                            "volatility": volatility,
                            "related_queries_count": related_query_count,
                            "rising_queries_count": rising_queries_count,
                            
                            # Meta information
                            "timeframe_analyzed": "12 months",
                            "data_points": len(interest_12m_df),
                            "search_consistency": "high" if volatility < 15 else "medium" if volatility < 30 else "low"
                        }
                        
                        workflows.append({
                            "workflow_name": f"Search Trend: {keyword}",
                            "platform": "Google Trends",
                            "country": country,
                            "popularity_metrics": metrics,
                            "source_url": f"https://trends.google.com/trends/explore?q={keyword.replace(' ', '%20')}&geo={country}"
                        })
                    else:
                        print(f"    -> No data available for '{keyword}' in {country}")
                    
                    break # Success, exit the retry loop

                except ResponseError as e:
                    print(f"    -> WARN: Request for '{keyword}' failed with {e.response.status_code}. Attempt {attempt + 1} of {retries}.")
                    if e.response.status_code == 429:
                        wait_time = (attempt + 1) * 5  # Wait 5s, then 10s, then 15s
                        print(f"    -> Rate limited. Waiting for {wait_time} seconds before retrying...")
                        time.sleep(wait_time)
                    else:
                        break # Don't retry for other errors
                except Exception as e:
                    print(f"    -> ERROR: An unexpected error occurred for keyword '{keyword}'. Reason: {e}")
                    break
            # --- End of retry logic ---
            time.sleep(2) # Longer delay between different keywords to avoid rate limits

    print(f"Found {len(workflows)} potential trends from Google.")
    return workflows