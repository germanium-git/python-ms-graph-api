from dotenv import load_dotenv
import requests
import msal
import os
import json
import atexit

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = "https://login.microsoftonline.com/" + TENANT_ID

REDIRECT_URI = "http://localhost"  # Redirect URI configured in Azure app
SCOPES = ["https://graph.microsoft.com/.default"]  # Scope for Microsoft Graph API


# Cache location
cache_filename = 'my_cache.json'

# Create a SerializableTokenCache object
cache = msal.SerializableTokenCache()

if os.path.exists(cache_filename):
       cache.deserialize(open(cache_filename, "r").read())
atexit.register(lambda:
    open(cache_filename, "w").write(cache.serialize())
    # Hint: The following optional line persists only when state changed
    if cache.has_state_changed else None
    )


# Create an MSAL Public client application
app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)


# Function to acquire token interactively (initial token acquisition)
def acquire_token_interactive():
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise ValueError("Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))

    print(flow["message"])

    result = app.acquire_token_by_device_flow(flow)


    if "access_token" in result:
        print("Access token acquired interactively.")
        return result
    else:
        print("Failed to acquire token interactively.")
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))
        return None

# Function to call Microsoft Graph API
def call_graph_api(token):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    graph_api_url = 'https://graph.microsoft.com/v1.0/me'

    response = requests.get(graph_api_url, headers=headers)

    if response.status_code == 200:
        print("Graph API call succeeded.")
        user = response.json()
        print(f"Hello {user['displayName']}, your email is {user['mail']}")
    else:
        print("Graph API call failed.")
        print(response.status_code)
        print(response.json())


# Function to acquire token silently
def acquire_token_silent(account):
    result = app.acquire_token_silent(SCOPES, account=account)
    if "access_token" in result:
        print("Access token acquired silently.")
        return result
    else:
        print("Failed to acquire token silently.")
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))
        return None


if __name__ == "__main__":
    # Attempt to acquire token silently first
    accounts = app.get_accounts()
    if accounts:
        print("Token cache exists")
        print("Using the last account from cache:", accounts[-1]['username'])
        print(json.dumps(accounts, indent=4))
        answer = input("Do you want to re-use this account? Enter yes or no: ")
        if answer.lower() == "yes":
            token_result = acquire_token_silent(accounts[-1])
        else:
            token_result = acquire_token_interactive()
    else:
        token_result = acquire_token_interactive()

    # Use the access token to call Microsoft Graph API or other protected resources
    if token_result and "access_token" in token_result:
        access_token = token_result["access_token"]
        call_graph_api(access_token)
