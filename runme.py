import asyncio
import string
import random
import sys
import os
import json
import threading
from nio import (
    AsyncClient,
    LoginResponse,
    InviteEvent,
    MatrixRoom,
)
from aiohttp import web
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

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

# Load configuration from config.json
with open("config.json", "r") as file:
    config = json.load(file)
    homeserver_url = config["homeserver_url"]
    user_id = config["user_id"]
    password = config["password"]

def get_image_url(url):
    # Set up headless Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--window-size=1920,1080")

    # Initialize the WebDriver
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Load the page
        driver.get(url)

        # Wait for the image to load
        driver.implicitly_wait(10)

        # Find the image element by id
        image_element = driver.find_element(By.ID, 'screenshot-image')

        # Extract the 'src' attribute
        image_url = image_element.get_attribute('src')

        # Handle cases where the image URL is invalid
        if not image_url or 'imageshack' in image_url:
            print("Image URL is invalid or not available.")
            return None

        # Handle relative URLs if necessary
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        elif image_url.startswith('/'):
            image_url = 'https://prnt.sc' + image_url

        return image_url

    except Exception as e:
        print(f"Error getting image URL: {e}")
        return None

    finally:
        driver.quit()

async def main():
    client = AsyncClient(homeserver_url, user_id)

    # Start the keep-alive server in a background task
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

    # Add the invite callback
    client.add_event_callback(on_invite, InviteEvent)

    # Start syncing in the background
    async def sync_loop():
        while True:
            await client.sync(timeout=30000)
            await asyncio.sleep(1)

    asyncio.create_task(sync_loop())

    loop = asyncio.get_event_loop()

    try:
        while True:
            try:
                # Generate a random string of 5 lowercase characters
                random_suffix = "".join(random.choices(string.ascii_lowercase, k=5))

                # Prepend the suffix with "s"
                random_string = "s" + random_suffix

                # Print the current random string being tested
                print(f"Testing {random_string}...")

                # Get the Short URL
                short_url = "https://prnt.sc/" + random_string

                # Run get_image_url in a separate thread to avoid blocking the event loop
                image_url = await loop.run_in_executor(None, get_image_url, short_url)

                if image_url:
                    # Prepare the message content
                    # Plain text body
                    message_text = f"Screenshot found at {random_string}"

                    # Formatted body with the image URL hyperlinked to the random_string
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
                    print("Could not retrieve image URL.")
                    await asyncio.sleep(1)
                    continue

                # Sleep for 1 second before generating the next URL
                await asyncio.sleep(1)

            except Exception as e:
                # Print any exceptions that occur
                print(f"Exception occurred: {e}")

                # Wait for 30 seconds before restarting the loop
                await asyncio.sleep(30)

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
