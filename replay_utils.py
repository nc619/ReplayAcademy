import numpy as np
import os, base64, requests, json
from time import sleep
import image_processing as IP
import cv2
import matplotlib.pyplot as plt
from itertools import product

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

def extendHPCol(col, extend_by = 1):
    out_col = col.copy()
    combinations = list(product([i for i in range(-extend_by,extend_by+1)],[i for i in range(-extend_by,extend_by+1)],[i for i in range(-extend_by,extend_by+1)]))
    for key in col:
        out_col[key] = []
        for pixel in col[key]:
            if len(pixel) == 0: continue
            for combination in combinations:
                out_col[key].append(list(map(int,list(np.array(pixel)+combination))))
    return out_col

#HERERES
HP_col = {'red3840': [[ 95,  49,  46],
       [101,  49,  47],
       [110,  56,  53],
       [111,  56,  53],
       [112,  56,  53],
       [112,  56,  54],
       [116,  53,  50],
       [117,  53,  50],
       [119,  57,  54],
       [120,  56,  54],
       [121,  56,  55],
       [127,  61,  58],
       [149,  70,  68],
       [150,  69,  68],
       [150,  70,  68],
       [156,  73,  72],
       [174,  80,  80],
       [176,  81,  81],
       [185,  84,  83],
       [185,  85,  83],
       [205,  93,  93],
       [208,  94,  94]],
          'red3840_strict': [[119,  57,  54],
       [120,  56,  54],
       [121,  56,  55],
       [149,  70,  68],
       [150,  69,  68],
       [150,  70,  68],
       [185,  84,  83],
       [185,  85,  83],
       [205,  93,  93],
       [208,  94,  94]],
          'blue3840': [[ 25,  48,  62],
       [ 25,  49,  63],
       [ 26,  44,  60],
       [ 31,  59,  78],
       [ 37,  71,  96],
       [ 38,  71,  98],
       [ 39,  77, 102],
       [ 41,  77, 106],
       [ 42,  78, 108],
       [ 44,  84, 115],
       [ 44,  84, 116],
       [ 44,  84, 117],
       [ 44,  85, 116],
       [ 44,  89, 120],
       [ 44,  90, 119],
       [ 44,  90, 120],
       [ 45,  89, 121],
       [ 48,  96, 129],
       [ 55, 110, 150],
       [ 55, 111, 149],
       [ 55, 111, 150],
       [ 56, 109, 150],
       [ 59, 116, 158],
       [ 65, 127, 177],
       [ 66, 129, 179],
       [ 68, 133, 185],
       [ 68, 134, 185],
       [ 68, 135, 185],
       [ 76, 147, 205],
       [ 76, 148, 205],
       [ 77, 149, 208]],
          'blue3840_strict': [[ 44,  89, 120],
       [ 44,  90, 119],
       [ 44,  90, 120],
       [ 45,  89, 121],
       [ 55, 110, 150],
       [ 55, 111, 149],
       [ 55, 111, 150],
       [ 56, 109, 150],
       [ 68, 133, 185],
       [ 68, 134, 185],
       [ 68, 135, 185],
       [ 76, 147, 205],
       [ 76, 148, 205],
       [ 77, 149, 208]],
          'red1920': [[208, 94, 94],
            [197, 89, 89],
            [197, 90, 89],
            [143, 66, 64],
            [142, 66, 64],
            [141, 66, 64],
            [121, 56, 55],
            [121, 57, 54],
            [122, 55, 55],
            [143, 65, 65],     
            [119, 57, 54],
            [119, 55, 54]],
          'blue1920': [[77,149,208],
           [73, 143, 197],
           [73, 142, 197],
           [52, 105, 141],
           [53, 104, 143],
           [53, 102, 143],
           [44, 90, 119],
           [45, 89, 121],
           [45, 87, 122],
           [44, 88, 119],
           [52, 104, 142],
           [52, 104, 141],
           ],
          'red960': [[]],
          'blue960': [[]],
          'hud_filler' : [[19, 19, 19]]}
# HP_col = extendHPCol(HP_col,1)
up_down_col = {'hp': (np.array([0, 140, 50]), np.array([18, 255, 90])),
               'xp': (np.array([174,  0, 246]), np.array([214, 111, 255])),
               'mana': (np.array([30, 96, 209]), np.array([82, 213, 255]))}

no_mana = ['Aatrox', 'Akali', 'Bel\'Veth', 'Briar', 'Dr. Mundo', 'Garen', 'Gnar', 'Katarina', 'Kennen', 'Kled', 'Lee Sin', 'Mordekaiser', 'Rek\'Sai', 'Renekton', 'Rengar', 'Riven', 'Rumble', 'Sett', 'Shen', 'Shyvana', 'Tryndamere', 'Viego', 'Vladimir', 'Yasuo', 'Yone', 'Zac', 'Zed']

def getChampPos(names, time = None):
    out_dict = {}
    for name in names:
        editDirector('render', {'cameraAttached': True,
                                'cameraMode': 'fps',
                                'selectionName': name,
                                'selectionOffset': {"x": 0.0, "y": 0.0, "z": 0.0,}})
        out_dict[name] = getDirector('render').json()['cameraPosition']
        out_dict[name] = {"x": out_dict[name]['x'], "z": out_dict[name]['z']}
    return out_dict

def getChampStatus(names,res, time = None, types = ['hp', 'mana', 'xp']):
    champ_dict = {}
    for name in names:
        champ_dict[name] = {}
        for type in types:
            # if champs[name] in no_mana and type == 'mana': continue
            champ_dict[name][type] = getChampBar(name, type, res, time)
    return champ_dict

def mapHUD(H_new, x_0, y_0, res = '1920', H_old = 0):
    if res == '3840':
        a1,b1,c1 = -0.00026497, -1.65894, 469.664
        a2,b2,c2 = 0.00011806, 2.07904, 404.044
    elif res == '1920':
        a1,b1,c1 = 0.000297378506, -0.871987906, 234.776357
        a2,b2,c2 = -0.0000185854412, 1.03969139, 201.422701
    x_up = lambda H : a1*(H**2) + b1*H + c1
    y_right = lambda H: a2*(H**2) + b2*H + c2
    if res == '3840':
        im_height = 800
    elif res == '1920':
        im_height = 400
    
    r_x0 = (x_0-x_up(H_old))/(im_height-x_up(H_old))
    x_new = x_up(H_new)+r_x0*(im_height-x_up(H_new))
    r_y0 = y_0/y_right(H_old)
    y_new = r_y0*y_right(H_new)
    return (int(np.round(x_new)), int(np.round(y_new)))
    
def getChampBar(name, type, res, time = None):
    editDirector('render', {'interfaceAll': True})
    editDirector('render', {'selectionName': name})

    # max_attempts = 3
    # for i in range(max_attempts):
        # try: 
    sleep(0.1)
    multipliers = {'1920': 2, '3840': 4, '960': 0.5, '2560': 2.6667}
    im = np.array(IP.getScreenshot(None, res))[-int(200*multipliers[res]):,:int(250*multipliers[res])]
    empty_mask = IP.applyColourMask(im, HP_col['hud_filler'])
    lower_col, upper_col = up_down_col[type]
    bar_mask = cv2.inRange(im,lower_col, upper_col) 
    contours, _ = cv2.findContours(bar_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        editDirector('render', {'interfaceAll': False})
        return 0
    rectangles = [cv2.boundingRect(contour) for contour in contours]
    x,y,w,h = max(rectangles, key=lambda r: r[2] * r[3])
    if h < 5*multipliers[res] and w < 5*multipliers[res]:
        editDirector('render', {'interfaceAll': False})
        return 0
    bar_length = w
    if type == 'hp' or type == 'mana':
        bar_empty = empty_mask[y+multipliers[res], x+w:]
    else:
        bar_empty = empty_mask[y+multipliers[res], x+w:]
    bar_empty_length = np.where(bar_empty == 0)[0].min()-1
    bar_percent = bar_length/(bar_length+bar_empty_length)
    editDirector('render', {'interfaceAll': False})
        # except Exception as e:
        #     print(e)
        #     continue

    return bar_percent

def getHUDScale(name, res = '1920'):
    editDirector('render', {'interfaceAll': True})
    editDirector('render', {'selectionName': name})
    sleep(0.1)
    multipliers = {'1920': 2, '3840': 4, '960': 0.5, '2560': 2.6667}
    ap_icon = np.load('assets/ap_icon.npy')
    im = np.array(IP.getScreenshot(None, res))[-int(200*multipliers[res]):,:int(250*multipliers[res])]
    x0, y0 = 248, 155
    x1, y1 = 257, 164
    similarities = []
    for H in range(101):
        x0_new, y0_new = mapHUD(H, x0, y0, res)
        x1_new, y1_new = mapHUD(H, x1, y1, res)
        # downsample the icon
        ap_icon_ds = cv2.resize(ap_icon, (x1_new-x0_new, y1_new-y0_new))
        similarities.append(np.sum(np.abs(ap_icon_ds-im[y0_new:y1_new,x0_new:x1_new])))
    return similarities, np.argmin(similarities)

def changeTime(time, delay):
    editDirector('playback', {'time': time-delay, 'paused': False})
    sleep(delay)
    editDirector('playback', {'paused': True})

def allLaneStats(time, zoom_factor = 3000, res = '1920', delay = 0.8):
    # editDirector('playback', {'time': time, 'paused': True})
    if time < 65:
        return -1
    editDirector('render', topView)
    editDirector('render', {type_dict['minion']: True})
    changeTime(time,delay)
    # sleep(5)
    im = np.array(IP.getScreenshot(None,res))
    final_centroids = {}
    Ms = {'1920': 30, '3840': 120, '2560': 60}
    min_sampless = {'1920': 125, '3840': 500, '2560': 250}
    for side in ['red', 'blue']:
        masked_im = IP.applyColourMask(im, HP_col[f'{side}{res}'])
        centroids = IP.findClusters2(masked_im, M = Ms[res], min_samples=min_sampless[res])
        s_final_centroids = getMostForward(centroids, side, 'image', res)
        for key in s_final_centroids:
            final_centroids[f'{side}_{key}'] = s_final_centroids[key]

    lane_stats = {key: {} for key in ['top', 'mid', 'bot']}
    for lane in lane_stats:
        lane_stats[lane] = getLaneStat(lane, time, res, 'multi', zoom_factor, final_centroids, delay = delay)
    return lane_stats
    
def getLaneStat(lane, time, res = '1920', mode = 'single', zoom_factor = 3000, final_centroids = None, delay = 0.8):
    if time < 65:
        return -1
    if mode == 'single':
        final_centroids = {}
        changeTime(time,delay)
        editDirector('render', topView)
        editDirector('render', {type_dict['minion']: True})
        Ms = {'1920': 30, '3840': 120, '2560': 60}
        min_sampless = {'1920': 125, '3840': 500, '2560': 250}
        for side in ['red', 'blue']:
            im = np.array(IP.getScreenshot(None), res)
            masked_im = IP.applyColourMask(im, HP_col[f'{side}{res}'])
            centroids = IP.findClusters2(masked_im, M = Ms[res], min_samples=min_sampless[res])
            s_final_centroids = getMostForward(centroids, side, 'image', res)
            for key in s_final_centroids:
                final_centroids[f'{side}_{key}'] = s_final_centroids[key]
    elif mode == 'multi' and type(final_centroids) == type(None):
        raise("Error in the inputs")
    lane_stat = {}
    lane_stat['fight_location'] = getFightLocation(final_centroids[f'blue_{lane}'], final_centroids[f'red_{lane}'], 'spec', res)
    lane_stat['blue'], lane_stat['red'] = {}, {}        
    for side in ['red', 'blue']:
        if (final_centroids[f'{side}_{lane}'] == [-1,-1]).all():
            lane_stat[side]['hpbars'] = np.array([])
            lane_stat[side]['nminion'] = 0
            lane_stat[side]['hptot'] = 0
            lane_stat[side]['location'] = [-1,-1]
        else:
            #
            try:
                zoomIn(final_centroids[f'{side}_{lane}'], zoom_factor,
                       position = f'{side}_{lane}',c_type = 'spec', res = res)
                im = np.array(IP.getScreenshot(None, res))
                results = IP.getBars(im, HP_col[f'{side}{res}'], res, first_flag = True)
            except:
                zoomIn(final_centroids[f'{side}_{lane}'], zoom_factor,
                       position = f'{side}_{lane}',c_type = 'spec',
                       res = res, change_rot = True)
                im = np.array(IP.getScreenshot(None, res))
                results = IP.getBars(im, HP_col[f'{side}{res}'], res, first_flag = False)
            lane_stat[side]['hpbars'] = results[0]
            lane_stat[side]['nminion'] = results[1]
            lane_stat[side]['hptot'] = results[0].sum()/100
            lane_stat[side]['location'] = final_centroids[f'{side}_{lane}']
            # lane_stat[f'{side}_hpbars'] = results[0]
            # lane_stat[f'{side}_nminion'] = results[1]
            # lane_stat[f'{side}_hptot'] =  results[0].sum()/100
    return lane_stat

def getFightLocation(blue_centroid, red_centroid, c_type = 'spec', res = '1920', threshold = 3000):
    if c_type == 'image':
        blue_centroid = imToSpec(blue_centroid, res)
        red_centroid = imToSpec(red_centroid, res)
    euclidian_dist = np.linalg.norm(np.array(blue_centroid) - np.array(red_centroid))
    if euclidian_dist > threshold:
        return (-1,-1)
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
        if len(full_coords['top']) == 0:
            final_centroids['top'] = np.array([-1,-1])
        else:
            top_idx = np.argsort(full_coords['top'][:,0])[::-1]
            if full_coords['top'].shape[0] == 1 or full_coords['top'][top_idx[-1],0] < 0.8*full_coords['top'][top_idx[-2],0]:
                final_centroids['top'] = full_coords['top'][top_idx[-1]]
            else:
                top_idx_idx = len(top_idx)-1-np.argmin([full_coords['top'][top_idx[-1],1], full_coords['top'][top_idx[-2],1]])
                final_centroids['top'] = full_coords['top'][top_idx[top_idx_idx]]
        if len(full_coords['mid']) == 0:
            final_centroids['mid'] = np.array([-1,-1])
        else:
            mid_idx = np.argsort(full_coords['mid'].sum(axis=1))[::-1]
            final_centroids['mid'] = full_coords['mid'][mid_idx[-1]]
        
        if len(full_coords['bot']) == 0:
            final_centroids['bot'] = np.array([-1,-1])
        else:
            bot_idx = np.argsort(full_coords['bot'][:,1])[::-1]
            if full_coords['bot'].shape[0] == 1 or full_coords['bot'][bot_idx[-1],1] < 0.8*full_coords['bot'][bot_idx[-2],1]:
                final_centroids['bot'] = full_coords['bot'][bot_idx[-1]]
            else:
                bot_idx_idx = len(bot_idx)-1-np.argmin([full_coords['bot'][bot_idx[-1],0], full_coords['bot'][bot_idx[-2],0]])
                final_centroids['bot'] = full_coords['bot'][bot_idx[bot_idx_idx]]
    elif side == 'blue':
        for coord in coords:
            lane = getLane(coord, 'spec', res)
            if lane not in full_coords:
                continue
            full_coords[lane].append(coord)
        full_coords = {key: np.array(full_coords[key]) for key in full_coords}
        # if full_coords['top']!=[]:
        if len(full_coords['top']) == 0:
            final_centroids['top'] = np.array([-1,-1])
        else:
            top_idx = np.argsort(full_coords['top'][:,0])
            if full_coords['top'].shape[0] == 1 or full_coords['top'][top_idx[-1],0] < 1.2*full_coords['top'][top_idx[-2],0]:
                final_centroids['top'] = full_coords['top'][top_idx[-1]]
            else:
                top_idx_idx = len(top_idx)-1-np.argmax([full_coords['top'][top_idx[-1],1], full_coords['top'][top_idx[-2],1]])
                final_centroids['top'] = full_coords['top'][top_idx[top_idx_idx]]
        
        if len(full_coords['mid']) == 0:
            final_centroids['mid'] = np.array([-1,-1])
        else:
            mid_idx = np.argsort(full_coords['mid'].sum(axis=1))
            final_centroids['mid'] = full_coords['mid'][mid_idx[-1]]
        
        if len(full_coords['bot']) == 0:
            final_centroids['bot'] = np.array([-1,-1])
        else:
            bot_idx = np.argsort(full_coords['bot'][:,1])
            if full_coords['bot'].shape[0] == 1 or full_coords['bot'][bot_idx[-1],1] < 1.2*full_coords['bot'][bot_idx[-2],1]:
                final_centroids['bot'] = full_coords['bot'][bot_idx[-1]]
            else:
                bot_idx_idx = len(bot_idx)-1-np.argmax([full_coords['bot'][bot_idx[-1],0], full_coords['bot'][bot_idx[-2],0]])
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

#HERERES

# bluespec_3840: {'x': 258.2060546875, 'y': 457.6369323730469, 'z': 321.2897033691406}
# redspec_3840: {'x': 14313.693359375, 'y': 411.1864318847656, 'z': 14698.1328125}
# blueimage_3840: (1090,260)
# redimage_3840: (2760, 1940)
def imToSpec(coords, res):
    if res == '3840':
        y,x = coords
        y = abs(y-2160)
        z_spec = int((y-260)*(14000/1680)+250)
        x_spec = int((x-1090)*(14000/1670)+250)
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

def zoomIn(coords, zoom = 3000, api_url="https://127.0.0.1:2999/replay", 
           verify = "riotgames.pem", position = "", c_type = 'spec', res = '1920',
           change_rot = False):
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
        'blue_top': {"x": 169.3003692626953, "y": 80, "z": 0.0},
            } 
    if change_rot:
        if position in ['red_top', 'blue_top', 'red_bot']:
            rotations[position]['x'] -= 30
        elif position in ['red_mid', 'blue_mid']:
            rotations[position]['x'] -= 20
        elif position in ['blue_bot']:
            rotations[position]['x'] += 20
    editDirector('render', {'cameraPosition': {'x': x_spec, 'y': zoom, 'z': z_spec}, 'cameraRotation': rotations[position]}, api_url, verify)
    sleep(0.4)

def getDirector(field, api_url="https://127.0.0.1:2999/replay", verify = "riotgames.pem"):
    r1 = requests.get(f"{api_url}/{field}", verify=verify)
    return r1

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