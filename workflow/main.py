import asyncio
from workflow.update_sheet import main as update_sheet_main
from x import main as x_main

async def main():
    # Call the main function from update_sheet.py
    companies = await update_sheet_main()
    #this will tweet all the companies
    x_main(companies)

if __name__ == "__main__":
    asyncio.run(main())