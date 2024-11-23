import json
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve Supabase URL and API key from environment variables
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(url, key)

# Load data from the JSON file
with open('S24.json', 'r') as file:
    companies_data = json.load(file)

# Insert data into Supabase
for company in companies_data:
    # Prepare the data for insertion
    data_to_insert = {
        "yc_page_url": company["yc_page_url"],
        "company_name": company["company_name"],
        "founded_year": company["founded_year"],
        "team_size": company["team_size"],
        "location": company["location"],
        "tags": company["tags"],  # This will be stored as JSONB
        "logo": company["logo"],
        "description": company["description"],
        "founders": company["founders"],  # This will be stored as JSONB
        "company_url": company["company_url"],
        "company_socials": company["company_socials"]
    }

    # Insert the data into the startuprxiv table
    response = supabase.table("startuprxiv").insert(data_to_insert).execute()
    print(f"Inserted: ", response)