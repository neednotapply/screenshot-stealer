import asyncio
import string
import random
import sys
import os
import json
import threading
from aiohttp import web
from nio import (
    AsyncClient,
    LoginResponse,
    InviteEvent,
    MatrixRoom,
)

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

    try:
        while True:
            try:
                # Generate a random string of 5 lowercase characters
                random_suffix = "".join(random.choices(string.ascii_lowercase, k=5))

                # Prepend the suffix with "s"
                random_string = "s" + random_suffix

                # Print the current random string being tested
                print(f"Testing {random_string}...")

                # Get the URL of the subdirectory
                url = "https://prnt.sc/" + random_string

                # Send the URL to all joined rooms
                for room_id in client.rooms:
                    content = {
                        "msgtype": "m.text",
                        "body": f"Sent to URL: {url}"
                    }
                    await client.room_send(
                        room_id=room_id,
                        message_type="m.room.message",
                        content=content
                    )
                    print(f"Sent to room {room_id}: {url}")

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
