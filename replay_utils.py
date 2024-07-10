import numpy as np
import os, base64, requests, json
from time import sleep
import image_processing as IP

topView = {
    'cameraMode': 'fps',
    'farClip': 35000,
    'cameraPosition': {'x': 7250, 'y': 25000, 'z': 7250},
    'cameraRotation': {'x': 0, 'y': 90,'z': 0},
    'cameraMoveSpeed': 5000,
    'healthBarChampions': False,
    'healthBarMinions': False,
    'healthBarPets': False,
    'healthBarStructures': False,
    'healthBarWards': False,
    'interfaceAll': False,
}
type_dict = {
    'minion': 'healthBarMinions',
    'champion': 'healthBarChampions',
    'pet': 'healthBarPets',
    'structure': 'healthBarStructures',
    'ward': 'healthBarWards'
}
HP_col = {'red1920': [[208, 94, 94],
            [197, 89, 89],
            [197, 90, 89],
            [143, 66, 64],
            [141, 66, 64],
            [121, 56, 55],
            [121, 57, 54],
            [119, 57, 54]],
          'blue1920': [[77,149,208],
           [73, 143, 197],
           [73, 142, 197],
           [52, 105, 141],
           [53, 104, 143],
           [44, 90, 119],
           [45, 89, 121]],
          'red960': [[]],
          'blue960': [[]]}

def allLaneStats(time, zoom_factor = 3000, res = '1920'):
    # editDirector('playback', {'time': time, 'paused': True})
    editDirector('render', topView)
    editDirector('render', {type_dict['minion']: True})
    im = np.array(IP.getScreenshot(None))
    final_centroids = {}
    for side in ['red', 'blue']:
        masked_im = IP.applyColourMask(im, HP_col[f'{side}{res}'])
        centroids = IP.findClusters2(masked_im)
        s_final_centroids = getMostForward(centroids, side, 'image', res)
        for key in s_final_centroids:
            final_centroids[f'{side}_{key}'] = s_final_centroids[key]

    lane_stats = {key: {} for key in ['top', 'mid', 'bot']}
    for key in final_centroids:
        side, lane = key.split('_')
        lane_stats[key] = getLaneStat(lane, time, res, 'multi', zoom_factor, final_centroids)
    return lane_stats
    
def getLaneStat(lane, time, res = '1920', mode = 'single', zoom_factor = 3000, final_centroids = None):
    if mode == 'single':
        final_centroids = {}
        for side in ['red', 'blue']:
            editDirector('playback', {'time': time, 'paused': True})
            editDirector('render', topView)
            editDirector('render', {type_dict['minion']: True})
            im = np.array(IP.getScreenshot(None))
            masked_im = IP.applyColourMask(im, HP_col[f'{side}{res}'])
            centroids = IP.findClusters2(masked_im)
            s_final_centroids = getMostForward(centroids, side, 'image', res)
            for key in s_final_centroids:
                final_centroids[f'{side}_{key}'] = s_final_centroids[key]
    elif mode == 'multi' and type(final_centroids) == type(None):
        raise("Error in the inputs")
    lane_stat = {}
    lane_stat['fight_location'] = getFightLocation(final_centroids[f'blue_{lane}'], final_centroids[f'red_{lane}'], 'spec', res)
    for side in ['red', 'blue']:
        zoomIn(final_centroids[f'{side}_{lane}'], zoom_factor, position = f'{side}_{lane}',c_type = 'spec', res = res)
        im = np.array(IP.getScreenshot(None))
        results = IP.getBars(im, HP_col[f'{side}{res}'], res)
        lane_stat[f'{side}_hpbars'] = results[0]
        lane_stat[f'{side}_nminion'] = results[1]
        lane_stat[f'{side}_hptot'] =  results[0].sum()/100
    return lane_stat

def getFightLocation(blue_centroid, red_centroid, c_type = 'spec', res = '1920', threshold = 3000):
    if c_type == 'image':
        blue_centroid = imToSpec(blue_centroid, res)
        red_centroid = imToSpec(red_centroid, res)
    euclidian_dist = np.linalg.norm(np.array(blue_centroid) - np.array(red_centroid))
    if euclidian_dist > threshold:
        return (0,0)
    else:
        return ((blue_centroid[0]+red_centroid[0])/2, (blue_centroid[1]+red_centroid[1])/2)
    
def getMostForward(coords, side = 'red', c_type = 'spec', res = '1920'):
    in_coords = coords
    if c_type == 'image':
        coords = [imToSpec(coord, res) for coord in coords]
    full_coords = {'top': [], 'mid': [], 'bot': []}
    final_centroids = {'top': [], 'mid': [], 'bot': []}
    if side == 'red':
        for coord in coords:
            lane = getLane(coord, 'spec', res)
            if lane not in full_coords:
                continue
            full_coords[lane].append(coord)
        full_coords = {key: np.array(full_coords[key]) for key in full_coords}
        top_idx = np.argsort(full_coords['top'][:,0])[::-1]
        if full_coords['top'].shape[0] == 1 or full_coords['top'][top_idx[-1],0] < 0.8*full_coords['top'][top_idx[-2],0]:
            final_centroids['top'] = full_coords['top'][top_idx[-1]]
        else:
            top_idx_idx = len(top_idx_idx)-np.argmin([full_coords['top'][top_idx[-1],1], full_coords['top'][top_idx[-2],1]])
            final_centroids['top'] = full_coords['top'][top_idx[top_idx_idx]]
        
        mid_idx = np.argsort(full_coords['mid'].sum(axis=1))[::-1]
        final_centroids['mid'] = full_coords['mid'][mid_idx[-1]]
        
        bot_idx = np.argsort(full_coords['bot'][:,1])[::-1]
        if full_coords['bot'].shape[0] == 1 or full_coords['bot'][bot_idx[-1],1] < 0.8*full_coords['bot'][bot_idx[-2],1]:
            final_centroids['bot'] = full_coords['bot'][bot_idx[-1]]
        else:
            bot_idx_idx = len(bot_idx_idx)-np.argmin([full_coords['bot'][bot_idx[-1],0], full_coords['bot'][bot_idx[-2],0]])
            final_centroids['bot'] = full_coords['bot'][bot_idx[bot_idx_idx]]
    elif side == 'blue':
        for coord in coords:
            lane = getLane(coord, 'spec', res)
            if lane not in full_coords:
                continue
            full_coords[lane].append(coord)
        full_coords = {key: np.array(full_coords[key]) for key in full_coords}
        # if full_coords['top']!=[]:
        top_idx = np.argsort(full_coords['top'][:,0])
        if full_coords['top'].shape[0] == 1 or full_coords['top'][top_idx[-1],0] < 1.2*full_coords['top'][top_idx[-2],0]:
            final_centroids['top'] = full_coords['top'][top_idx[-1]]
        else:
            top_idx_idx = len(top_idx_idx)-np.argmax([full_coords['top'][top_idx[-1],1], full_coords['top'][top_idx[-2],1]])
            final_centroids['top'] = full_coords['top'][top_idx[top_idx_idx]]
        mid_idx = np.argsort(full_coords['mid'].sum(axis=1))
        final_centroids['mid'] = full_coords['mid'][mid_idx[-1]]
        
        bot_idx = np.argsort(full_coords['bot'][:,1])
        if full_coords['bot'].shape[0] == 1 or full_coords['bot'][bot_idx[-1],1] < 1.2*full_coords['bot'][bot_idx[-2],1]:
            final_centroids['bot'] = full_coords['bot'][bot_idx[-1]]
        else:
            bot_idx_idx = len(bot_idx_idx)-np.argmax([full_coords['bot'][bot_idx[-1],0], full_coords['bot'][bot_idx[-2],0]])
            final_centroids['bot'] = full_coords['bot'][bot_idx[bot_idx_idx]]
    return final_centroids

def getLane(coords, c_type = 'spec', res = '1920'):
    if c_type == 'image':
        coords = imToSpec(coords, res)
    x, z = coords
    top_A_x, top_A_z = 2500, 5500
    top_B_x, top_B_z = 9500, 11500
    bot_A_x, bot_A_z = 5000, 3000
    bot_B_x, bot_B_z = 12000, 9500
    if (z < 4500 and x < 4500):
        return 'blue_base'
    elif (z > 10500 and x > 10500):
        return 'red_base'
    elif (top_B_x - top_A_x) * (z - top_A_z) - (top_B_z - top_A_z) * (x - top_A_x) > 0:
        return 'top'
    elif (bot_B_x - bot_A_x) * (z - bot_A_z) - (bot_B_z - bot_A_z) * (x - bot_A_x) > 0:
        return 'mid'
    else:
        return 'bot'

def imToSpec(coords, res):
    if res == '1920':
        y,x = coords
        print(y)
        print(x)
        y = abs(y-1080)
        z_spec = int((y-125)*(14000/845)+250)
        x_spec = int((x-525)*(14000/865)+250)
    elif res == '960':
        y,x = coords
        y = abs(y-540)
        z_spec = int((y-60)*(14000/420)+250)
        x_spec = int((x-265)*(14000/425)+250)
    return (x_spec, z_spec)

def specToIm(coords):
    x,z = coords
    y = int((z-250)*(420/14000)+60)
    y = abs(y-540)
    x = int((x-250)*(425/14000)+265)
    return (y,x)

def zoomIn(coords, zoom = 3000, api_url="https://127.0.0.1:2999/replay", verify = "riotgames.pem", position = "", c_type = 'spec', res = '1920'):
    if c_type == 'image':
        coords = imToSpec(coords, res)
    x_spec,z_spec = coords
    x_spec,z_spec = float(x_spec), float(z_spec)
    # 'cameraRotation': {'x': 225, 'y': 85,'z': 0}
    rotations = {
        'red_bot': {"x": 169.3003692626953, "y": 74.00001525878906, "z": 0.0},
        'red_mid': {'x': 178.30038452148438, 'y': 76.00000762939453, 'z': 0.0},
        'red_top': {'x': 208.30030822753906, 'y': 75.00001525878906, 'z': 0.0},
        'blue_bot': {"x": 169.3003692626953, "y": 74.00001525878906, "z": 0.0},
        'blue_mid': {"x": 169.3003692626953, "y": 74.00001525878906, "z": 0.0},
        'blue_top': {"x": 169.3003692626953, "y": 74.00001525878906, "z": 0.0},
            } 
    
    editDirector('render', {'cameraPosition': {'x': x_spec, 'y': zoom, 'z': z_spec}, 'cameraRotation': rotations[position]}, api_url, verify)

def editDirector(field, data, api_url="https://127.0.0.1:2999/replay", verify = "riotgames.pem"):
    r1 = requests.post(f"{api_url}/{field}", verify=verify,json=data)
    return r1

def getLcuCredentials(riot_path = "C:/Riot Games/League of Legends/"):
    with open(riot_path + "lockfile", "r") as f:
        lines = f.readlines()
    line = next(iter(lines))
    fields = line.split(":")
    port = fields[2]
    password = fields[3]
    enc_str = str(base64.b64encode(("riot:"+password).encode('utf-8')),'utf-8')
    return port, enc_str

def openReplay(replayID,port, authorization_header):
    headers = {
    'accept': '*/*',
    'Authorization': f'Basic {authorization_header}',
    'Content-Type': 'application/json',
    }
    json_data = {
        'componentType': 'string',
    }

    response = requests.post(
        f'https://127.0.0.1:{port}/lol-replays/v1/rofls/{replayID}/watch',
        headers=headers,
        json=json_data,
        verify=False,
    )
    return response

def get_latest_log_file(log_directory):
    folders = [os.path.join(log_directory, f) for f in os.listdir(log_directory)]
    latest_folder = max(folders, key=os.path.getctime)
    files = [os.path.join(latest_folder, f) for f in os.listdir(latest_folder)]
    latest_file = max(files, key = os.path.getctime)
    return latest_file

def is_replay_loading(riot_path = "C:/Riot Games/League of Legends/"):
    log_file = get_latest_log_file(riot_path + "Logs/GameLogs")
    with open(log_file, "r") as file:
        file.seek(0, os.SEEK_END)
        while True:
            line = file.readline()
            if not line:
                sleep(1)  # Wait for new data
                continue
            # Check for specific log entries that indicate the replay is loading
            if "LoadingScreen complete" in line:
                print("Replay has finished loading.")
                sleep(3)
                break
            else:
                print("Replay is still loading...")