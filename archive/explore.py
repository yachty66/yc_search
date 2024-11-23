import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright  # Import Playwright
import time
import random
import json

urls = [
    'https://www.ycombinator.com/companies?batch=F24',
    'https://www.ycombinator.com/companies?batch=S24',
    'https://www.ycombinator.com/companies?batch=W24',
    'https://www.ycombinator.com/companies?batch=S23',
    'https://www.ycombinator.com/companies?batch=W23',
    'https://www.ycombinator.com/companies?batch=S22',
    'https://www.ycombinator.com/companies?batch=W22',
    'https://www.ycombinator.com/companies?batch=S21',
    'https://www.ycombinator.com/companies?batch=W21',
    'https://www.ycombinator.com/companies?batch=S20',
    'https://www.ycombinator.com/companies?batch=W20',
    'https://www.ycombinator.com/companies?batch=S19',
    'https://www.ycombinator.com/companies?batch=W19',
    'https://www.ycombinator.com/companies?batch=S18',
    'https://www.ycombinator.com/companies?batch=W18',
    'https://www.ycombinator.com/companies?batch=S17',
    'https://www.ycombinator.com/companies?batch=W17',
    'https://www.ycombinator.com/companies?batch=IK12',
    'https://www.ycombinator.com/companies?batch=S16',
    'https://www.ycombinator.com/companies?batch=W16',
    'https://www.ycombinator.com/companies?batch=S15',
    'https://www.ycombinator.com/companies?batch=W15',
    'https://www.ycombinator.com/companies?batch=S14',
    'https://www.ycombinator.com/companies?batch=W14',
    'https://www.ycombinator.com/companies?batch=S13',
    'https://www.ycombinator.com/companies?batch=W13',
    'https://www.ycombinator.com/companies?batch=S12',
    'https://www.ycombinator.com/companies?batch=W12',
    'https://www.ycombinator.com/companies?batch=S11',
    'https://www.ycombinator.com/companies?batch=W11',
    'https://www.ycombinator.com/companies?batch=S10',
    'https://www.ycombinator.com/companies?batch=W10',
    'https://www.ycombinator.com/companies?batch=S09',
    'https://www.ycombinator.com/companies?batch=W09',
    'https://www.ycombinator.com/companies?batch=S08',
    'https://www.ycombinator.com/companies?batch=W08',
    'https://www.ycombinator.com/companies?batch=S07',
    'https://www.ycombinator.com/companies?batch=W07',
    'https://www.ycombinator.com/companies?batch=S06',
    'https://www.ycombinator.com/companies?batch=W06',
    'https://www.ycombinator.com/companies?batch=S05'
]

# List of User-Agents
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    # Add more User-Agents as needed
]

def fetch_company_links(url):
    user_agent = random.choice(user_agents)  # Select a random User-Agent
    batch = url.split('=')[-1]  # Extract the batch from the URL
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Launch headless browser
        context = browser.new_context(user_agent=user_agent)  # Set User-Agent
        page = context.new_page()  # Create a new page
        page.goto(url)  # Navigate to the URL

        # Scroll to the bottom of the page
        last_height = page.evaluate("document.body.scrollHeight")  # Get the initial height

        while True:
            # Scroll down to the bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)  # Wait for new content to load

            # Calculate new height and compare with last height
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:  # If heights are the same, we've reached the bottom
                break
            last_height = new_height  # Update last height

        time.sleep(5)  # Wait for a bit before closing

        # Extract all company profile URLs
        company_links = page.query_selector_all('a._company_86jzd_338')  # Select all company links
        urls = [(link.get_attribute('href'), batch) for link in company_links]  # Extract href attributes and associate with batch

        context.close()  # Close the context
        browser.close()  # Close the browser
        return urls  # Return the extracted URLs and their batches

# List to hold all company URLs with their batches
all_company_urls = []

# Use ThreadPoolExecutor to fetch URLs in parallel
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(fetch_company_links, url): url for url in urls}
    for future in as_completed(futures):
        all_company_urls.extend(future.result())  # Collect results

# Print or process the combined URLs with their batches
# Save the combined URLs with their batches to a file
with open('company_urls.txt', 'w') as file:
    for company_url, batch in all_company_urls:
        file.write(f"Batch: {batch}, URL: {company_url}\n")  # Write each entry to the file

print("Results have been saved to company_urls.txt")  # Indicate completion