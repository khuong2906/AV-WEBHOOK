import logging
from PIL import Image, ImageGrab # pillow
from io import BytesIO
import json
import os
import time
from discord_webhook import DiscordWebhook, DiscordEmbed
try:
    import pyautogui # cause of opencv for confidence
except ImportError:
    os.system("pip install pyautogui opencv-python")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

with open("config.json", "r") as config_file:
    config = json.load(config_file)
show_full_screen = config.get("screenshot_full_screen",False)

def send_webhook(webhook_url, embed, content, screenshot):
    webhook = DiscordWebhook(webhook_url, content=content)
    webhook.add_embed(embed)
    embed.set_thumbnail(url="https://static.wikia.nocookie.net/rbx-anime-vanguards/images/7/71/AnimeVanguards.png/revision/latest?cb=20240531035940")
    embed.set_timestamp()
    if screenshot:
        with open("screenshot.png", 'rb') as f:
            webhook.add_file(file=f.read(), filename='screenshot.png')
        embed.set_image(url="attachment://screenshot.png")

    response = webhook.execute()
    if screenshot:
        os.remove('screenshot.png')
    logging.info("Webhook message sent successfully.")
if show_full_screen == False:
    import pygetwindow as gw


def capture_window(window_title):
    try:
        if show_full_screen == True:
            screenshot = ImageGrab.grab()
        else:
            roblox_window = next((win for win in gw.getWindowsWithTitle(window_title)), None)
            if roblox_window:
                bbox = (roblox_window.left + 10, roblox_window.top + 10, roblox_window.right - 10, roblox_window.bottom - 10)
                screenshot = ImageGrab.grab(bbox)
            else:
                logging.warning(f"Window titled '{window_title}' not found. Using placeholder image.")
                screenshot = Image.open('placeholder.png') 
        return screenshot
    except Exception as e:
        logging.error(f"Error capturing window '{window_title}': {e}. Using placeholder image.")
        return Image.open('placeholder.png')

player_ping_string = ""
player_ids = config.get("player_id_to_ping", [])
for i in player_ids:
    player_ping_string = f"{player_ping_string}<@{i}> "
if not config.get("ping_players", False):
    player_ping_string = ""
logging.info(f"Players to ping: '{player_ping_string}'")

image_prototypes = ["replay1.png", "replay2.png", "return1.png", "return2.png"] 
checkcooldown = config.get("resend_timeout", 100)
send_webhook_delay = config.get("send_webhook_delay",0.5)
screenshot_delay = config.get("screenshot_delay",0.5)

last_webhook_sent = 0
webhooks_sent = 1

while True:
    try:
        for image_file in image_prototypes:
            button_location = pyautogui.locateCenterOnScreen(image_file, confidence=0.7)
            if button_location:
                logging.info(f"Found image: '{image_file}' at {button_location}")
                try:
                    time.sleep(screenshot_delay)
                    screenshot = capture_window("Roblox")
                    if screenshot:
                        screenshot_path = 'screenshot.png'
                        if os.path.exists(screenshot_path):
                            os.remove(screenshot_path)
                        
                        image_bytes = BytesIO()
                        screenshot.save(image_bytes, format='PNG')
                        image_bytes.seek(0)

                        with open(screenshot_path, 'wb') as f:
                            f.write(image_bytes.getvalue())
                    description_text = f"``` ```\n> # Map Finished!\n> ## {webhooks_sent} Webhook Update{'s' if webhooks_sent != 1 else ''} Sent!"

                    if webhooks_sent != 1:
                        time_now = time.time()  
                        time_elapsed = time_now - last_webhook_sent 
                        minutes, seconds = divmod(time_elapsed, 60)
    
                        logging.info(f"Time since last update: {int(minutes)} minutes, {seconds:.2f} seconds")
                        description_text = f"{description_text}\n> ### Time since last update: {int(minutes)} minutes, {seconds:.2f} seconds."
    
                        last_webhook_sent = time_now  
                    else:
                        last_webhook_sent = time.time()


                    embed = DiscordEmbed(
                        title="Game Finish UI Spotted!",
                        description=description_text
                    )
                    
                    
                    logging.info("Found Finished Game UI, making Discord Embed!")
                    time.sleep(send_webhook_delay)
                    for webhook_url in config.get("discord_webhook", []):
                        send_webhook(webhook_url, embed, player_ping_string, screenshot)
                    webhooks_sent += 1
                    logging.info(f"Waiting {checkcooldown}s before sending another message.")
                    time.sleep(checkcooldown) 
                except Exception as img_error:
                    logging.error(f"Error capturing or sending screenshot: {img_error}")
            time.sleep(0.1)
    except Exception as er:
        logging.error(f"Error: {er}")
        time.sleep(1)
    
    time.sleep(0.1)
