import os
import time
import json
from dotenv import load_dotenv
from openai import OpenAI
import tweepy

# Load environment variables
load_dotenv()

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def create_tweet(company):
    company_name = company["name"]
    company_description = company["description"]
    company_url = company["url"]
    twitter_profiles = " ".join([f"@{founder['socials']['Twitter'].split('/')[-1]}" for founder in company["founders"] if "Twitter" in founder["socials"] and founder['socials']['Twitter'] != "Not available"])

    prompt = f"""
    You need to create a tweet. You are given the following information:

    - Company name: {company_name}
    - Company description: {company_description}
    - Company URL: {company_url}
    - Twitter profiles: {twitter_profiles}

    Please return a JSON object as follows:
    {{
        "🏷️": "{company_name}",
        "📜": "[short summary of description]",
        "👤": "{twitter_profiles}",
        "🔗": "{company_url}"
    }}
    """

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    response = completion.choices[0].message.content
    return json.loads(response)

def post_tweet(tweet):
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret_key = os.getenv("TWITTER_API_SECRET_KEY")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    client = tweepy.Client(
        consumer_key=api_key, consumer_secret=api_secret_key,
        access_token=access_token, access_token_secret=access_token_secret
    )

    try:
        client.create_tweet(text=tweet)
    except Exception as e:
        print(f"Failed to create tweet: {str(e)}")

def main(company_data):
    company_data = json.loads(company_data)  # Convert JSON string to Python object
    for company in company_data:
        tweet_data = create_tweet(company)
        tweet_parts = [f"{key}: {value}" for key, value in tweet_data.items() if value != "Not available"]
        tweet = "\n".join(tweet_parts)

        # Check tweet length and adjust if necessary
        if len(tweet) > 270:
            tweet_parts = [part for part in tweet_parts if not part.startswith("📜")]
            tweet = "\n".join(tweet_parts)

        post_tweet(tweet)
        time.sleep(600)  # Optional delay to avoid hitting rate limits