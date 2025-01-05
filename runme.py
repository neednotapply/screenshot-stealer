import asyncio
import string
import random
import sys
import os
import json
from aiohttp import web, ClientSession
from nio import (
    AsyncClient,
    LoginResponse,
    InviteEvent,
    MatrixRoom,
)
from playwright.async_api import async_playwright
import time

# File where we store tested codes for persistence
TESTED_CODES_FILE = "tested_codes.txt"

async def handle_root(request):
    return web.Response(text="Bot is running.")

async def start_keep_alive():
    app = web.Application()
    app.add_routes([web.get('/', handle_root)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

# Load configuration
with open("config.json", "r") as file:
    config = json.load(file)
    homeserver_url = config["homeserver_url"]
    user_id = config["user_id"]
    password = config["password"]

def load_tested_codes(filepath: str) -> set:
    """
    Load tested codes from a file into a set.
    If the file doesn't exist or is empty, return an empty set.
    """
    tested = set()
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    code = line.strip()
                    if code:
                        tested.add(code)
        except Exception as e:
            print(f"Error loading tested codes from file: {e}")
    return tested

def append_tested_code(filepath: str, code: str):
    """
    Append a single tested code to the file.
    """
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(code + "\n")
    except Exception as e:
        print(f"Error appending tested code {code}: {e}")

async def get_image_url(url: str) -> str:
    """
    Launch a headless browser with Playwright,
    load the given URL, and extract the image src.
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)

            # Wait for the screenshot image to appear (up to 5 seconds)
            await page.wait_for_selector("#screenshot-image", timeout=5000)

            # Get the 'src' attribute of the image
            image_url = await page.get_attribute("#screenshot-image", "src")

            await browser.close()

            if image_url:
                # Handle potential relative URLs
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                elif image_url.startswith('/'):
                    image_url = 'https://prnt.sc' + image_url
                return image_url

    except Exception as e:
        print(f"Error getting image URL: {e}")

    return None

async def validate_image_url(image_url: str) -> bool:
    """
    Perform a HEAD request to check if the image URL is valid (status code 200).
    """
    try:
        async with ClientSession() as session:
            async with session.head(image_url, timeout=5) as response:
                if response.status == 200:
                    return True
                print(f"Image URL {image_url} returned status {response.status}")
    except Exception as e:
        print(f"Error validating image URL {image_url}: {e}")

    return False

async def main():
    # Load previously tested codes from file
    tested_codes = load_tested_codes(TESTED_CODES_FILE)
    print(f"Loaded {len(tested_codes)} previously tested codes from {TESTED_CODES_FILE}")

    client = AsyncClient(homeserver_url, user_id)
    asyncio.create_task(start_keep_alive())

    # Login to the Matrix server
    response = await client.login(password)
    if isinstance(response, LoginResponse):
        print("Login successful")
    else:
        print(f"Failed to login: {response}")
        return

    # Define an event callback for invites
    async def on_invite(room: MatrixRoom, event: InviteEvent):
        room_id = room.room_id
        print(f"Received invite to {room_id}, attempting to join...")
        await client.join(room_id)

    client.add_event_callback(on_invite, InviteEvent)

    async def sync_loop():
        while True:
            await client.sync(timeout=30000)
            await asyncio.sleep(1)

    asyncio.create_task(sync_loop())

    try:
        while True:
            try:
                # Generate a new random code that hasn't been tested yet
                random_string = None
                while True:
                    # Generate a random 5-letter suffix
                    random_suffix = "".join(random.choices(string.ascii_lowercase, k=5))
                    candidate = "s" + random_suffix
                    if candidate not in tested_codes:
                        tested_codes.add(candidate)
                        # Append to file immediately
                        append_tested_code(TESTED_CODES_FILE, candidate)
                        random_string = candidate
                        break
                    else:
                        # If we've tested it already, generate another
                        continue

                # Print the current random string being tested
                print(f"Testing {random_string}...")

                # Construct the short URL
                short_url = "https://prnt.sc/" + random_string

                # Get the image URL with Playwright
                image_url = await get_image_url(short_url)

                if image_url and await validate_image_url(image_url):
                    # Plain text body (includes the image URL for preview)
                    message_text = f"Screenshot found at {random_string}\n{image_url}"

                    # HTML body (clean presentation)
                    html_content = f'Screenshot found at <a href="{image_url}">{random_string}</a>'

                    content = {
                        "msgtype": "m.text",
                        "body": message_text,
                        "format": "org.matrix.custom.html",
                        "formatted_body": html_content,
                    }

                    # Send the message to all joined rooms
                    for room_id in client.rooms:
                        await client.room_send(
                            room_id=room_id,
                            message_type="m.room.message",
                            content=content
                        )
                        print(f"Sent to room {room_id}: {random_string} -> {image_url}")
                else:
                    print(f"Skipping invalid or 404 image URL for {random_string}")

                # Add a random delay to avoid getting rate-limited
                delay = random.uniform(3, 7)  # 3 to 7 seconds
                print(f"Sleeping for {delay:.2f} seconds to avoid rate-limiting...")
                await asyncio.sleep(delay)

            except Exception as e:
                print(f"Exception occurred: {e}")
                await asyncio.sleep(30)

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
