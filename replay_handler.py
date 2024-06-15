import requests
import json
import numpy as np
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import os, pathlib
from screenshot import getScreenshot

def editDirector(field, data, api_url="https://127.0.0.1:2999", verify = "riotgames.pem"):
    r1 = requests.post(f"{api_url}/{field}", verify=verify,json=data)
    return r1
    
def openReplay(replayID):
    
    headers = {
    'accept': '*/*',
    'Authorization': 'Basic cmlvdDpMemZDU3pwZ0lfUkJtNDBnNnlXdFVR',
    'Content-Type': 'application/json',
    }
    json_data = {
        'componentType': 'string',
    }

    response = requests.post(
        f'https://127.0.0.1:56868/lol-replays/v1/rofls/{replayID}/watch',
        headers=headers,
        json=json_data,
        verify=False,
    )


# def checkEnableApi(config_path = "RA_config.txt"):
#     if not os.path.exists(config_path):
#         try: 
#             pre_path = f"{pathlib.Path.home().drive}/Riot Games/League of Legends/Config/game.cfg"
#             path = askopenfilename(filetypes = [('Config Files', '.cfg')], initialfile=pre_path, initialdir=pre_path, title = 'Select Riot Games\League of Legends\Config\game.cfg')
#         except: 
#             path = askopenfilename(filetypes = [('Config Files', '.cfg')], title = 'Select Riot Games\League of Legends\Config\game.cfg')

#         # Open the file in read mode and read all lines
#         try:
#             with open(path, "r") as f:
#                 lines = f.readlines()

#             # Iterate over the lines and replace as necessary
#             for i, line in enumerate(lines):
#                 if "EnableReplayApi=" in line:
#                     if "EnableReplayApi=0" in line:
#                         lines[i] = "EnableReplayApi=1\n"
#                     # else:
#                         # lines[i] = "EnableReplayApi=1\n"

#             # Open the file in write mode and write the modified lines
#             with open(path, "w") as f:
#                 f.writelines(lines)
#             with open(config_path, "w") as f:
#                 f.write("EnableAPI=1\n")
#             return 0
#         except:
#             with open(config_path, "w") as f:
#                 f.write("EnableAPI=0\n")
#             return 1
#     else: 
#         with open(config_path, "r") as f:
#             lines = f.readlines()
#         for line in lines:
#             if "EnableAPI=" in line:
#                 if "EnableAPI=1" in line:
#                     return 0
#                 else:
#                     return 1

# if checkEnableApi() == 1:
#     exit()

api_url = "https://127.0.0.1:2999/replay"

render_fields = {'banners': True, # (bool): Haven't figure out what this is
        'cameraAttached': False, # (bool): Camera is attached or not
        'cameraLookSpeed': [], # (float): Speed at which camera rotates
        'cameraMode': [], # (str): Camera mode (i.e. top/fps)
        'cameraMoveSpeed': [], # (float): Speed at which camera moves
        'cameraPosition': [], # (dict[floats]: x, y, z): x, y, z position of camera, where x is left/right, y is up/down, z is forward/backward
        'cameraRotation': [], # (dict[floats]: x, y, z): x, y, z rotation of camera, where x is pitch, y is yaw, z is roll
        'characters': [], # (bool): Characters are visible or not
        'depthFogColor': [], # (dict[floats]: a, r, g, b): a is alpha and r, g, b is color of depth fog
        'depthFogEnabled': [], # (bool): Depth fog is enabled or not
        'depthFogEnd': [], # (float): End of depth fog
        'depthFogIntensity': [], # (float): Intensity of depth fog
        'depthFogStart': [], # (float): Start of depth fog
        'depthOfFieldCircle': [], # (float): Circle of depth of field size
        'depthOfFieldDebug': [], # (bool): Depth of field debug is enabled or not
        'depthOfFieldEnabled': [], # (bool): Depth of field is enabled or not
        'depthOfFieldFar': [], # (float): Not sure
        'depthOfFieldMid': [], # (float): Not sure
        'depthOfFieldNear': [], # (float): Not sure
        'depthOfFieldWidth': [], # (float): Not sure
        'environment': [], # (bool): Environment (every terrain on the map) is visible or not
        'farClip': [], # (float): Maximum distance the camera can see
        'fieldOfView': [], # (float): Field of view of camera, didn't see changes when changing this
        'floatingText': [], # (bool): Didn't see any changes with this 
        'fogOfWar': [], # (bool): Fog of war is visible or not
        'healthBarChampions': [], # (bool): Health bars of champions are visible or not
        'healthBarMinions': [], # (bool): Health bars of minions are visible or not
        'healthBarPets': [], # (bool): Health bars of pets are visible or not
        'healthBarStructures': [], # (bool): Health bars of structures are visible or not
        'healthBarWards': [], # (bool): Health bars of wards are visible or not
        'heightFogColor': [], # (dict[floats]: a, r, g, b): a is alpha and r, g, b is color of height fog
        'heightFogEnabled': [], # (bool): Height fog is enabled or not
        'heightFogEnd': [], # (float): End of height fog
        'heightFogIntensity': [], # (float): Intensity of height fog
        'heightFogStart': [], # (float): Start of height fog
        'interfaceAll': [], # (bool): All interfaces are visible or not
        'interfaceAnnounce': [], # (bool): Announce interface is visible or not
        'interfaceChat': [], # (bool): Chat interface is visible or not
        'interfaceFrames': [], # (bool): Champions at the right/left of screen interface is visible or not
        'interfaceKillCallouts': [], # (bool): Kill callouts interface is visible or not
        'interfaceMinimap': [], # (bool): Minimap interface is visible or not
        'interfaceNeutralTimers': [], # (bool): Neutral timers interface is visible or not (DEFAULT: OFF)
        'interfaceQuests': [], # (bool): Quests interface is visible or not
        'interfaceReplay': [], # (bool): Bottom-left replay interface is visible or not
        'interfaceScore': [], # (bool): Top score interface is visible or not
        'interfaceScoreboard': [], # (bool): Bottom pulable replay scoreboard interface is visible or not
        'interfaceTarget': [], # (bool): Not sure what this does
        'interfaceTimeline': [], # (bool): Bottom timeline interface is visible or not
        'navGridOffset': [], #(bool): NON-REVERSIBLE!??!?!: Creates an offset for the entities with respect to the map
        'nearClip': [], # (float): Minimum distance the camera can see (do not change)
        'outlineHover': [], # (bool): Not sure what this does
        'outlineSelect': [], # (bool): Not sure what this does
        'particles': [], # (bool): Particles are visible or not
        'selectionName': [], # (str): Allows you to choose who is selected. Can GET minion selection but cannot POST it
        'selectionOffset': [], # (dict[floats]: x, y, z): x, y, z, puts you at an offset location from selection        'skyboxOffset': [], 
        'skyboxOffset': [], # (float): Changes skybox offset, useless (background changes)
        'skyboxPath': [], # (str): Path to skybox
        'skyboxRadius': [], # (float): Changes skybox radius, useless (background changes)
        'skyboxRotation': [], # (float): Changes skybox rotation, useless (background changes)
        'sunDirection': []} # (dict[floats]: x, y, z): x, y, z, changes direction of sun

game_fields = {
    'processID': [], # (int): ID of the game
}

playback_fields = {
    'length': [], # (float): Length of the replay in seconds
    'paused': [], # (bool): Is the replay paused or not
    'seeking': [], # (bool): Idk what it does, it remains on False
    'speed': [], # (float): Speed of the replay
    'time': [], # (float): Time of the replay in seconds
}

recording_fields = {
    'codec': [], # (str): Codec of the recording (what compresses/decompresses)
    'currentTime': [], # (float): Current time of the recording in seconds
    'endTime': [], # (float): End time of the recording in seconds | -1.0 by default
    'enforceFrameRate': [], # (bool): Enforce frame rate or not
    'framesPerSecond': [], # (int): Frames per second of the recording
    'height': [], # (int): Height of the recording
    'lossless': [], # (bool): Lossless recording or not
    'path': [], # (str): Path of the recording
    'recording': [], # (bool): Recording or not
    'replaySpeed': [], # (float): Replay speed of the recording
    'startTime': [], # (float): Start time of the recording in seconds | -1.0 by default
    'width': [] # (int): Width of the recording
}

type_dict = {
    'minon': 'healthBarMinions',
    'champion': 'healthBarChampions',
    'pet': 'healthBarPets',
    'structure': 'healthBarStructures',
    'ward': 'healthBarWards'
}

sequence_fields = {
    # I don't think we need sequences, if we do i'll figure it out.
}

r = requests.get(f"{api_url}/render", verify="riotgames.pem")   
# cameraData = {'banners': True}
# r1=requests.post(f"{api_url}/render", verify="riotgames.pem",json=cameraData)
pass

blue_fountain = {'x': 235, 'y': 300, 'z': 260}
red_fountain = {'x': 14500, 'y': 300, 'z': 14500}
# top_position = {'cameraRotation': {'x': 225, 'y': 85,'z': 0}}
# top_position['cameraPosition'] = {}
# for key in blue_fountain:
    # top_position['cameraPosition'][key] = (red_fountain[key]-blue_fountain[key])/2-blue_fountain
cameraData = {
    'cameraMode': 'fps',
    'farClip': 35000,
    'cameraPosition': {'x': 9000, 'y': 22000, 'z': 9000},
    'cameraRotation': {'x': 225, 'y': 85,'z': 0},
    'cameraMoveSpeed': 5000,
    'healthBarChampions': False,
    'healthBarMinions': False,
    'healthBarPets': False,
    'healthBarStructures': False,
    'healthBarWards': False,
    'interfaceAll': False,
}
editDirector('render', cameraData)

event_time = 300.0
editDirector('playback', {'time': event_time})

get_type = 'minion'
editDirector('render', {type_dict[get_type]: True})


