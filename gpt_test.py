import requests
import subprocess
import os
import time

def get_lcu_credentials():
    # Path to the lockfile
    lockfile_path = os.path.expandvars(r'C:\Riot Games\League of Legends\lockfile')
    
    if not os.path.exists(lockfile_path):
        raise FileNotFoundError(f"Lockfile not found at {lockfile_path}")
    
    # Read the lockfile
    with open(lockfile_path, 'r') as file:
        data = file.read().split(':')
        return {
            "port": data[2],
            "password": data[3],
            "protocol": data[4]
        }

def open_replay(replay_file_path):
    # Ensure the replay file exists
    if not os.path.exists(replay_file_path):
        raise FileNotFoundError(f"Replay file not found at {replay_file_path}")
    
    # Get LCU credentials
    credentials = get_lcu_credentials()
    credentials['port'] = 56868
    credentials['password'] = 'cmlvdDpMemZDU3pwZ0lfUkJtNDBnNnlXdFVR'
    # Set up the request URL and headers
    replay_ID = replay_file_path.split('-')[-1].split('.')[0]
    url = f"https://127.0.0.1:{credentials['port']}/lol-replays/v1/rofls/{replay_ID}/watch"
    headers = {
        'accept': '*/*',
        "Authorization": f"Basic {credentials['password']}",
        'Content-Type': 'application/json',
    }
    json_data = {
        'componentType': 'string',
    }
    # Create the payload for the request
    payload = {
        "path": replay_file_path
    }
    print(url)
    # Send the request to the LCU API
    response = requests.post(url, headers=headers, verify=False, json = json_data)
    
    if response.status_code == 201:
        print("Replay file opened successfully.")
    else:
        print(f"Failed to open replay file: {response.status_code} - {response.text}")

# Example usage
replay_file_path = r"C:\Users\Nico\Documents\League of Legends\Replays\EUW1-6966295035.rofl"

# Wait for the League of Legends client to be fully loaded
# time.sleep(30)
open_replay(replay_file_path)