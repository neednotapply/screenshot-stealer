import asyncio
import string
import random
import sys
import os
import json
from aiohttp import web
from nio import (
    AsyncClient,
    LoginResponse,
    InviteEvent,
    MatrixRoom,
)
from playwright.async_api import async_playwright

# Keep Alive Functionality
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

            # Wait for the screenshot image to appear (optional)
            await page.wait_for_selector("#screenshot-image", timeout=5000)

            # Get the 'src' attribute of the image
            image_url = await page.get_attribute("#screenshot-image", "src")

            await browser.close()

            if image_url:
                # Fix relative URLs if needed
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                elif image_url.startswith('/'):
                    image_url = 'https://prnt.sc' + image_url
                return image_url

    except Exception as e:
        print(f"Error getting image URL: {e}")

    return None

async def main():
    client = AsyncClient(homeserver_url, user_id)

    asyncio.create_task(start_keep_alive())

    # Login
    response = await client.login(password)
    if isinstance(response, LoginResponse):
        print("Login successful")
    else:
        print(f"Failed to login: {response}")
        return

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
                random_suffix = "".join(random.choices(string.ascii_lowercase, k=5))
                random_string = "s" + random_suffix
                print(f"Testing {random_string}...")

                # Build the short URL
                short_url = "https://prnt.sc/" + random_string

                # Get image URL using Playwright
                image_url = await get_image_url(short_url)

                if image_url:
                    # Plain text body (for URL preview)
                    message_text = f"Screenshot found at {random_string}\n{image_url}"

                    # HTML body (clean presentation)
                    html_content = f'Screenshot found at <a href="{image_url}">{random_string}</a>'

                    content = {
                        "msgtype": "m.text",
                        "body": message_text,
                        "format": "org.matrix.custom.html",
                        "formatted_body": html_content,
                    }

                    for room_id in client.rooms:
                        await client.room_send(
                            room_id=room_id,
                            message_type="m.room.message",
                            content=content
                        )
                        print(f"Sent to {room_id}: {random_string} -> {image_url}")
                else:
                    print("Could not retrieve image URL.")
                    await asyncio.sleep(1)
                    continue

                await asyncio.sleep(1)

            except Exception as e:
                print(f"Exception occurred: {e}")
                await asyncio.sleep(30)

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
