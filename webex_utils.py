import os
import json
from wxc_sdk import WebexSimpleApi
from wxc_sdk.integration import Integration
from wxc_sdk.common import Greeting

# Load config
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def get_integration():
    config = load_config().get("webex", {})
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    redirect_uri = config.get("redirect_uri")
    
    if not all([client_id, client_secret, redirect_uri]):
        raise ValueError("OAuth not fully configured in config.json")
        
    return Integration(
        client_id=client_id,
        client_secret=client_secret,
        scopes=["spark:kms", "spark:telephony_config_read", "spark:telephony_config_write", "spark:people_read", "spark:people_write"],
        redirect_url=redirect_uri
    )

def get_api(access_token=None):
    if access_token:
        return WebexSimpleApi(tokens=access_token)
    
    config = load_config().get("webex", {})
    static_token = config.get("static_token")
    if static_token and static_token != "YOUR_STATIC_TEST_TOKEN":
        return WebexSimpleApi(tokens=static_token)
    
    raise ValueError("No access token or static token available")

def upload_voicemail_greetings(api: WebexSimpleApi, wav_file_path: str):
    """
    Uploads the given wav file as the busy and no answer greeting for the authenticated user.
    """
    # Get the authenticated user's ID
    me = api.people.me()
    person_id = me.person_id
    
    # 1. Upload the greetings
    api.person_settings.voicemail.configure_busy_greeting(person_id, content=wav_file_path)
    api.person_settings.voicemail.configure_no_answer_greeting(person_id, content=wav_file_path)
    
    # 2. Update settings to use the custom greetings
    # Read current settings to modify them
    settings = api.person_settings.voicemail.read(person_id)
    
    # Ensure voicemail is enabled
    if settings.enabled is False:
         settings.enabled = True
         
    # Update busy calls to use custom greeting
    if settings.send_busy_calls:
        settings.send_busy_calls.greeting = Greeting.custom
        settings.send_busy_calls.enabled = True
        
    # Update unanswered calls to use custom greeting
    if settings.send_unanswered_calls:
        settings.send_unanswered_calls.greeting = Greeting.custom
        settings.send_unanswered_calls.enabled = True

    api.person_settings.voicemail.configure(person_id, settings)
    
    return True
