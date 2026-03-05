import asyncio
import argparse
import yt_dlp
import subprocess
import os
from pathlib import Path
from playwright.async_api import async_playwright

async def download_video(url, name, season, episode):
    
    if name:
        filename = name        
    else :
        filename = url.rsplit('/', 1)[-1]
        
    if season:
        filename = filename + " s" + f"{season:02}" + "e" + f"{episode:02}"
    
    ydl_opts = {
        # 'bestvideo+bestaudio/best' ensures you get the highest quality
        'format': 'best',
        'outtmpl': f'{filename}.%(ext)s', # Name of the file
        'noplaylist': True,
        # Many sites need a specific user agent to not block the request
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"Starting download: {url}")
        ydl.download([url])

async def process_page(page, url, name, season):
    """Load a page and open all hrefs from divs with class 'thumb-under' in new tabs"""
    print(f"Processing URL: {url}")
    
    # Navigate to the main page
    await page.goto(url)
    
    # Wait for the page to load
    await page.wait_for_load_state('networkidle')
    
    # Find all divs with class 'thumb-under' and extract hrefs
    hrefs = await page.eval_on_selector_all(
        'li.grid__item a[href]',
        'elements => elements.map(el => el.href)'
    )
    
    # If none then the supplied url should contain the link
    if len(hrefs) == 0:
        hrefs.append(url)
    
    print(f"Found {len(hrefs)} links in li.grid__item")
    
    
    # Open each href in a new tab
    context = page.context
    currentNo = 1
    for href in hrefs:
        print(f"Downloading ({currentNo}/{len(hrefs)}: {href}") 
        await download_video(href, name, season, currentNo)        
        currentNo = currentNo + 1    
        
        
    # 1. Get the current directory of the script
    # If you want the folder where bbci.py lives:
    current_folder = Path(__file__).parent.resolve()

    # 2. Define the sub-folder path (this appends \x265 to the current path)
    destination_folder = current_folder / "x265"
    
    # Define the command as a list of arguments
    cmd = [
        "python", 
        "convertToH265.py", 
        str(current_folder), 
        str(destination_folder)
    ]

    try:
        # This will block bbci.py until the conversion script finishes
        result = subprocess.run(cmd, check=True, text=True)
        
        print("Script finished successfully!")
        print("Output:", result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the script: {e}")

async def main():
    """Main function to cycle through URLs and process them"""
    
    args = parse_arguments()
    
    headless = args.no_headless
    url = args.url
    
       
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=headless)  # Set to True for headless mode
        context = await browser.new_context()
        page = await context.new_page()
        
        # Process each URL
        await process_page(page, url, args.name, args.season)
        
        # Close browser
        await browser.close()
    
    
    

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='BBC iPlayer Downloader',
        epilog='''
        Examples:
        python bbci.py --url https://www.bbc.co.uk/iplayer/episodes/b03bxtqk/dragons --no-headless
        python bbci.py --url https://www.bbc.co.uk/iplayer/episodes/b03bxtqk/dragons --name "How To Train Your Dragon" --season 1 --no-headless
        python bbci.py --url https://www.bbc.co.uk/iplayer/episode/b069gxz7/bletchley-park-codebreakings-forgotten-genius
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--url', required=True, 
                       help='url')
    parser.add_argument('--name', required=False, 
                       help='name')
    parser.add_argument('--season', required=False, type=int,
                       help='season e.g. 1')
    parser.add_argument('--no-headless', action='store_true',
                       help='Run browser in visible mode (useful for debugging)')
    return parser.parse_args()

if __name__ == "__main__":
    
    # Run the script
    asyncio.run(main())