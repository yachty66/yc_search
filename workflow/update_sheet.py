import gspread
from datetime import datetime
import re
from oauth2client.service_account import ServiceAccountCredentials
import json
import time
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import nest_asyncio
import pandas as pd
from gspread_formatting import (
    DataValidationRule,
    BooleanCondition,
    set_data_validation_for_cell_range,
)


# Apply the nest_asyncio patch
nest_asyncio.apply()

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name("google.json", scope)
client = gspread.authorize(creds)

sheet = client.open("YC Insights").sheet1


async def main():
    last_batch = await get_last_batch()
    print("last batch is", last_batch)
    url = "https://www.ycombinator.com/companies?batch=" + last_batch
    print("url is", url)
    all_companies = await get_all_companies(url)
    print("all companies are", all_companies)
    missing_companies = get_missing_companies(all_companies)
    print("missing companies are", missing_companies)
    if missing_companies != []:
        # Run the main function and store the result in a variable
        company_info = asyncio.run(get_company_info(missing_companies))
        company_info_json = json.dumps(company_info, indent=2)
        print("company info is", company_info_json)
        company_info_data = json.loads(company_info_json)
        add_missing_data_to_sheet(company_info_data)
        updated_header()
        return json.dumps(company_info_data)  # Return as JSON string

async def get_last_batch():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # URL of the Y Combinator companies page
        url = "https://www.ycombinator.com/companies"
        await page.goto(url)

        # Wait for the page to load completely
        await page.wait_for_timeout(5000)  # Adjust the wait time as needed

        # Get the page source and parse it with BeautifulSoup
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")

        # Close the browser
        await browser.close()

        # Find the div with the class "_facet_86jzd_85" containing "All batches"
        facet_div = None
        divs = soup.find_all("div", class_="_facet_86jzd_85")
        for div in divs:
            if "All batches" in div.get_text():
                facet_div = div
                break

        if facet_div:
            # Find all the labels within the div
            labels = facet_div.find_all("label")

            # Extract the text of the last batch
            if labels:
                last_batch = (
                    labels[1].find("span", class_="_label_86jzd_224").get_text()
                )
                print(f"The name of the last batch is: {last_batch}")
            else:
                print("No batches found.")
        else:
            print("No div containing 'All batches' found.")
        return last_batch


async def get_all_companies(url):
    # get links of all companies from the page of the batch
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url)
        await page.wait_for_timeout(5000)  # Adjust the wait time as needed

        last_height = await page.evaluate("document.body.scrollHeight")

        while True:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await page.wait_for_timeout(2000)  # Adjust the wait time as needed

            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        content = await page.content()
        await browser.close()

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(content, "html.parser")

        # Find all anchor tags with the class "_company_86jzd_338"
        company_anchors = soup.find_all("a", class_="_company_86jzd_338")

        # Extract the href attribute from each anchor tag
        company_links = [
            anchor["href"] for anchor in company_anchors if "href" in anchor.attrs
        ]
        return company_links


def get_missing_companies(company_links):
    # identifying mising companies in the sheet
    # Get all values from the sheet
    data = sheet.get_all_values()

    # Skip the first two rows and use the third row as headers
    df = pd.DataFrame(data[2:], columns=data[1])  # Skip the first two rows for headers

    # Extract the URLs from the Google Sheet
    sheet_urls = df["URL"].tolist()

    # Normalize the URLs from the Google Sheet
    base_url = "https://www.ycombinator.com"
    normalized_sheet_urls = [url.strip() for url in sheet_urls]

    # Normalize the company links
    normalized_company_links = [base_url + link for link in company_links]

    # Check for missing URLs
    missing_urls = [
        url for url in normalized_company_links if url not in normalized_sheet_urls
    ]
    return missing_urls


async def scrape_company_data(context, url):
    page = await context.new_page()
    try:
        print(f"Navigating to {url}")
        await page.goto(url)
        print(f"Successfully navigated to {url}")

        company_data = {}

        # Save the company URL
        company_data["url"] = url

        # Get name
        print(f"Extracting company name from {url}...")
        company_name = await page.text_content("h1.font-extralight")
        company_data["name"] = (
            company_name.strip() if company_name else "Name not found"
        )
        print(f"Company name: {company_data['name']}")

        # Check if active
        print("Checking if company is active...")
        active_div_selector = "div.flex.flex-row.items-center.justify-between > div.mr-\[6px\].h-3.w-3.rounded-full.bg-green-500"
        active_div = await page.query_selector(active_div_selector)
        company_data["status"] = "Active" if active_div else "Not Active"
        print(f"Company is {company_data['status']}")

        # Get profile picture
        print("Extracting profile picture...")
        try:
            profile_picture = await page.wait_for_selector(
                "div.h-32.w-32.shrink-0.clip-circle-32 > img",
                state="attached",
                timeout=100,
            )
            company_data["profile_picture_url"] = (
                await profile_picture.get_attribute("src")
                if profile_picture
                else "Not available"
            )
        except Exception as e:
            print(f"Failed to find profile picture: {str(e)}")
            company_data["profile_picture_url"] = "Not available"
        print(f"Profile picture URL: {company_data['profile_picture_url']}")

        # Extract all tags
        print("Extracting tags...")
        tags_elements = await page.query_selector_all(
            "div.align-center.flex.flex-row.flex-wrap.gap-x-2.gap-y-2 > a"
        )
        company_data["tags"] = [
            await tag.text_content()
            for tag in tags_elements
            if await tag.text_content()
        ]
        print(f"Tags: {company_data['tags']}")

        # Get description
        print("Extracting description...")
        description = await page.text_content("p.whitespace-pre-line")
        company_data["description"] = (
            description.strip() if description else "Description not available"
        )

        # Extract batch from tags
        batch_tag = next((tag for tag in company_data["tags"] if "Y Combinator Logo" in tag), None)
        company_data["batch"] = batch_tag.replace("Y Combinator Logo", "").strip() if batch_tag else "Batch not found"
        print(f"Batch: {company_data['batch']}")

        print(f"Description: {company_data['description']}")

        # Extract foundational details, team size, and location
        print("Extracting foundational details, team size, and location...")
        founded_selector = (
            "div.ycdc-card > div.space-y-0\\.5 > div:nth-child(1) > span:last-child"
        )
        company_data["founded"] = await page.text_content(founded_selector)
        team_size_selector = (
            "div.ycdc-card > div.space-y-0\\.5 > div:nth-child(2) > span:last-child"
        )
        company_data["team_size"] = await page.text_content(team_size_selector)
        location_selector = (
            "div.ycdc-card > div.space-y-0\\.5 > div:nth-child(3) > span:last-child"
        )
        company_data["location"] = await page.text_content(location_selector)
        print(
            f"Founded: {company_data['founded']}, Team Size: {company_data['team_size']}, Location: {company_data['location']}"
        )

        # Get socials
        print("Extracting social media links...")
        socials = {}
        social_media_types = {
            "LinkedIn": 'a[aria-label="LinkedIn profile"]',
            "Twitter": 'a[aria-label="Twitter account"]',
            "Facebook": 'a[aria-label="Facebook profile"]',
            "Crunchbase": 'a[aria-label="Crunchbase profile"]',
            "GitHub": 'a[aria-label="Github profile"]',
        }
        for media, selector in social_media_types.items():
            try:
                href = await page.wait_for_selector(
                    selector, state="attached", timeout=100
                )
                socials[media] = (
                    await href.get_attribute("href") if href else "Not available"
                )
            except Exception as e:
                print(f"Failed to find {media} link: {str(e)}")
                socials[media] = "Not available"
        company_data["socials"] = socials
        print(f"Social media links: {company_data['socials']}")

        # Extract founders' data
        print("Extracting founders' data...")
        company_data["founders"] = await extract_founder_info(page)
        print(f"Founders Information: {company_data['founders']}")

        return company_data
    except Exception as e:
        print(f"Error occurred while processing {url}: {e}")
        return {"url": url, "error": str(e)}
    finally:
        await page.close()


async def extract_founder_info(page):
    founder_elements_selector = "div.flex.flex-row.items-center.gap-x-3"
    founder_elements = await page.query_selector_all(founder_elements_selector)
    print("Founders elements:", founder_elements)
    all_founders_data = []
    for founder in founder_elements:
        name = await founder.query_selector("div.font-bold")
        name_text = await name.text_content() if name else "Name not found"
        socials = {}
        social_media_types = {
            "LinkedIn": 'a[aria-label="LinkedIn profile"]',
            "Twitter": 'a[aria-label="Twitter account"]',
        }
        for media, selector in social_media_types.items():
            social_link = await founder.query_selector(selector)
            social_href = (
                await social_link.get_attribute("href")
                if social_link
                else "Not available"
            )
            socials[media] = social_href
        founder_data = {"name": name_text.strip(), "socials": socials}
        all_founders_data.append(founder_data)
    return all_founders_data


async def scrape_batch(context, urls):
    tasks = [scrape_company_data(context, url) for url in urls]
    return await asyncio.gather(*tasks)


async def get_company_info(missing_urls):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()

        start_index = 0
        url_list = missing_urls[start_index:]

        batch_size = 50  # Number of URLs to process at once
        all_data = []

        for i in range(0, len(url_list), batch_size):
            batch_urls = url_list[i : i + batch_size]
            batch_data = await scrape_batch(context, batch_urls)
            all_data.extend(batch_data)

        await browser.close()
        return all_data


def add_missing_data_to_sheet(company_info):
    # Use the scraped_data variable directly
    data = company_info

    # Start inserting data from row 4
    row_index = 3

    # Iterate over each row in the JSON data
    for row in data:

        # Extract the necessary fields
        name = row.get("name", "")
        profile_picture_url = row.get("profile_picture_url", "")
        url = row.get("url", "")
        status = row.get("status", "")
        tags = row.get("tags", [])[1:]  # Skip the first element
        tags_str = ", ".join(tags) if tags else "Not available"
        description = row.get("description", "")
        founded = row.get("founded", "")
        team_size = row.get("team_size", "")
        location = row.get("location", "")
        socials = row.get("socials", {})
        crunchbase = socials.get("Crunchbase", "")
        founders = row.get("founders", [])
        
        # Extract the batch information
        batch = row.get("batch", "Not available")  # Add this line to get the batch info

        # Prepare the founders' data
        founders_names = []
        founders_linkedin = []
        founders_twitter = []
        for founder in founders:
            founder_name = founder.get("name", "")
            founder_socials = founder.get("socials", {})
            founder_linkedin = founder_socials.get("LinkedIn", "")
            founder_twitter = founder_socials.get("Twitter", "")
            founders_names.append(founder_name)
            founders_linkedin.append(founder_linkedin)
            founders_twitter.append(founder_twitter)

        # Set the first founder as the default selection
        default_founder = founders_names[0] if founders_names else ""

        # Prepare the row data with the image formula
        row_data = [
            name,
            "",
            url,
            status,
            tags_str,
            description,
            founded,
            team_size,
            location,
            crunchbase,
            batch, 
            default_founder,
            "",
            ""
        ]
        print(row_data)
        sheet.insert_row(row_data, row_index)  # Insert at the current row index

        # Handle image formula
        if profile_picture_url != "Not available":
            image_formula = f'=IMAGE("{profile_picture_url}", 2)'
            sheet.update_acell(f"B{row_index}", image_formula)
        else:
            sheet.update_acell(f"B{row_index}", "Not available")

        # Add dropdown for founders if there are any
        if founders_names:
            # Add dropdown for founders
            cell_range = f"L{row_index}"
            validation_rule = DataValidationRule(
                BooleanCondition("ONE_OF_LIST", founders_names), showCustomUi=True
            )
            set_data_validation_for_cell_range(sheet, cell_range, validation_rule)

            # Create the nested IF formula for LinkedIn and Twitter
            if_formula_linkedin = ""
            if_formula_twitter = ""
            for name, linkedin in zip(founders_names, founders_linkedin):
                if_formula_linkedin += f'IF(L{row_index}="{name}", "{linkedin}", '
            if_formula_linkedin += '""' + ")" * len(founders_names)

            for name, twitter in zip(founders_names, founders_twitter):
                if_formula_twitter += f'IF(L{row_index}="{name}", "{twitter}", '
            if_formula_twitter += '""' + ")" * len(founders_names)

            # Add formulas to display selected founder's LinkedIn and Twitter
            sheet.update_acell(f"M{row_index}", f"={if_formula_linkedin}")
            sheet.update_acell(f"N{row_index}", f"={if_formula_twitter}")

        row_index += 1  # Increment the row index for the next insertion
        time.sleep(5)  # Optional: Add a delay to avoid hitting rate limits


def updated_header():
    # Update the header sheet
    header_cell = sheet.acell("A1").value
    current_date = datetime.now().strftime("%Y-%m-%d")
    # Regular expression to find the "Last update:" string and everything after it
    update_pattern = re.compile(r"Last update:.*")
    # Check if the header already contains "Last update:"
    if update_pattern.search(header_cell):
        updated_header = update_pattern.sub(f"Last update: {current_date}", header_cell)
    else:
        # Append the current date to the existing text
        updated_header = f"{header_cell} Last update: {current_date}"
    sheet.update_acell("A1", updated_header)


if __name__ == "__main__":
    asyncio.run(main())