"""
input is the url of a list of companies from a certain batch and I need to save the data inside a supabase database 
"""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright  # Import Playwright
import time
import random
import json

# Define the batch to filter
target_batch = "S24"

# List to hold companies from the specified batch
filtered_companies = []

# Read the company URLs from the file
with open('company_urls.txt', 'r') as file:
    for line in file:
        if f"Batch: {target_batch}" in line:  # Check if the line contains the target batch
            # Extract the company path from the line
            company_path = line.split(", URL: ")[-1].strip()  # Get the URL part
            filtered_companies.append(company_path)  # Add the company path to the list

# Convert filtered companies to full URLs
base_url = 'https://www.ycombinator.com'
urls = [f"{base_url}{company}" for company in filtered_companies]  # Construct full URLs

print(f"Number of companies identified in batch {target_batch}: {len(urls)}")

# List of User-Agents
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    # Add more User-Agents as needed
]

# List to hold all company data
all_companies_data = []

def extract_company_name(page):
    """Extract the company name using a CSS selector."""
    print("Extracting company name from page: ", page.url)  # Print the URL of the page being processed
    return page.locator('h1.font-extralight').inner_text()  # Use CSS selector to get the company name

def extract_founded_year(page):
    """Extract the year the company was founded."""
    print("Extracting founded year from page: ", page.url)  # Print the URL of the page being processed
    founded_year = page.locator('div.flex.flex-row.justify-between span:has-text("Founded:") + span').inner_text()
    return founded_year.strip()  # Return the founded year, stripping any extra whitespace

def extract_team_size(page):
    """Extract the team size using a CSS selector."""
    print("Extracting team size from page: ", page.url)  # Print the URL of the page being processed
    team_size = page.locator('div.flex.flex-row.justify-between span:has-text("Team Size:") + span').inner_text()
    return team_size.strip()  # Return the team size, stripping any extra whitespace

def extract_location(page):
    """Extract the location using a CSS selector."""
    print("Extracting location from page: ", page.url)  # Print the URL of the page being processed
    location = page.locator('div.flex.flex-row.justify-between span:has-text("Location:") + span').inner_text()
    return location.strip()  # Return the location, stripping any extra whitespace

def extract_tags(page):
    """Extract all tags from the page, including the 'Active' tag if present."""
    print("Extracting tags from page: ", page.url)  # Print the URL of the page being processed
    tags = page.locator('div.align-center.flex.flex-row.flex-wrap.gap-x-2.gap-y-2 a div.yc-tw-Pill').all_inner_texts()
    
    # Check for the "Active" tag
    active_tag = page.locator('div.align-center.flex.flex-row.flex-wrap.gap-x-2.gap-y-2 div:has-text("Active")')
    if active_tag.count() > 0:
        tags.append("Active")  # Add "Active" to the tags if it exists

    return [tag.strip() for tag in tags]

def extract_logo(page):
    """Extract the logo URL from the page."""
    print("Extracting logo from page: ", page.url)  # Print the URL of the page being processed
    try:
        # Use a more specific selector to find the logo with the S3 URL
        logo_url = page.locator('img.h-full.w-full[src^="https://bookface-images.s3.amazonaws.com"]').get_attribute('src')
        return logo_url.strip() if logo_url else None  # Return the logo URL, or None if not found
    except Exception as e:
        print(f"Error extracting logo: {e}")
        return None

def extract_description(page):
    """Extract the company description using a CSS selector."""
    print("Extracting description from page: ", page.url)  # Print the URL of the page being processed
    try:
        # Use a more specific selector to find the description
        description = page.locator('div.prose p.whitespace-pre-line').inner_text()  # Use CSS selector to get the description
        return description.strip()  # Return the description, stripping any extra whitespace
    except Exception as e:
        print(f"Error extracting description: {e}")
        return None

def extract_founders_socials(page):
    """Extract founders' names and their social media URLs from the page."""
    print("Extracting founders' names and socials from page: ", page.url)  # Print the URL of the page being processed
    founders = []
    
    try:
        # Locate all founder sections
        founder_elements = page.locator('div.space-y-5 > div.flex.flex-row.flex-col.items-start')
        
        for i in range(founder_elements.count()):
            founder_info = founder_elements.nth(i)
            name = founder_info.locator('h3.text-lg.font-bold').inner_text().strip()  # Extract founder's name
            
            # Initialize a dictionary to hold social links
            social_links = {}
            
            # Locate all social link elements
            social_elements = founder_info.locator('div.mt-1.space-x-2 a')
            for j in range(social_elements.count()):
                social_link = social_elements.nth(j)
                url = social_link.get_attribute('href')  # Get the URL
                title = social_link.get_attribute('title')  # Get the title (e.g., "LinkedIn profile", "Twitter account")
                
                if title:  # Only add if title is present
                    social_links[title] = url  # Store the URL with the title as the key
            
            founders.append({
                'name': name,
                'social_links': social_links  # Store all social links for the founder
            })
        
        return founders  # Return the list of founders
    except Exception as e:
        print(f"Error extracting founders' socials: {e}")
        return None
    
def extract_company_url(page):
    """Extract the company URL from the page."""
    print("Extracting company URL from page: ", page.url)  # Print the URL of the page being processed
    try:
        # Locate the anchor element containing the company URL
        company_url = page.locator('div.group a').get_attribute('href')
        return company_url.strip() if company_url else None  # Return the company URL, or None if not found
    except Exception as e:
        print(f"Error extracting company URL: {e}")
        return None

def extract_company_socials(page):
    """Extract company social media links from the page."""
    print("Extracting company socials from page: ", page.url)  # Print the URL of the page being processed
    socials = {}
    
    try:
        # Locate the div containing the social links for the company
        social_elements = page.locator('div.ycdc-card div.space-x-2 a')  # Adjust the selector to target the correct div
        
        for i in range(social_elements.count()):
            social_link = social_elements.nth(i)
            url = social_link.get_attribute('href')  # Get the URL
            title = social_link.get_attribute('title')  # Get the title (e.g., "LinkedIn profile", "Twitter account")
            
            if title:  # Only add if title is present
                socials[title] = url  # Store the URL with the title as the key
        
        return socials  # Return the dictionary of social links
    except Exception as e:
        print(f"Error extracting company socials: {e}")
        return None

def open_url(url):
    user_agent = random.choice(user_agents)  # Select a random User-Agent
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Launch headless browser
        context = browser.new_context(user_agent=user_agent)  # Set User-Agent
        page = context.new_page()  # Create a new page
        page.goto(url)  # Navigate to the URL

        time.sleep(5)  # Wait for a bit to ensure the page loads completely

        # Extract data
        company_data = {
            "yc_page_url": url,
            'company_name': extract_company_name(page),
            'founded_year': extract_founded_year(page),
            'team_size': extract_team_size(page),
            'location': extract_location(page),
            'tags': extract_tags(page),
            'logo': extract_logo(page),
            'description': extract_description(page),
            'founders': extract_founders_socials(page),
            'company_url': extract_company_url(page),
            'company_socials': extract_company_socials(page)
        }

        all_companies_data.append(company_data)  # Append the company data to the list

        context.close()  # Close the context
        browser.close()  # Close the browser

# Use ThreadPoolExecutor to open URLs in parallel
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(open_url, url): url for url in urls}
    for future in as_completed(futures):
        print(f"Processed number of companies: {len(all_companies_data)}")
        future.result()  # Wait for all futures to complete

number_of_companies = len(all_companies_data)
# Check if the number of URLs matches the number of companies collected
if len(urls) == number_of_companies:
    print("The number of identified companies matches the number of companies collected.")
else:
    print("The number of identified companies does not match the number of companies collected.")

# Save all collected data to a JSON file named after the batch
output_filename = f"{target_batch}.json"
with open(output_filename, 'w') as outfile:
    json.dump(all_companies_data, outfile, indent=4)

print(f"All URLs have been opened and processed. Data saved to {output_filename}.")  # Indicate completion