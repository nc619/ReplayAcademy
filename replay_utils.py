import numpy as np
import os, base64, requests, json
from time import sleep
import image_processing as IP
import cv2
import matplotlib.pyplot as plt
from itertools import product
from PIL import Image
import easyocr
from io import BytesIO
import psutil
import time

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
          'red2560': [[]],
          'blue2560': [[]],
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
    elif res == '2560':
        a1,b1,c1 = 2.63748974e-04, -1.16223481e+00,  3.14076784e+02
        a2,b2,c2 = 5.26188644e-07, 1.40076643e+00, 2.67981431e+02
        # a1,b1,c1 = 3.31852603e-04, -1.17249532e+00,  3.13956895e+02
        # a2,b2,c2 = -1.05239140e-04,  1.41173298e+00,  2.68911353e+02
    elif res == '1920':
        a1,b1,c1 = 0.000297378506, -0.871987906, 234.776357
        a2,b2,c2 = -0.0000185854412, 1.03969139, 201.422701
    x_up = lambda H : a1*(H**2) + b1*H + c1
    y_right = lambda H: a2*(H**2) + b2*H + c2
    if res == '3840':
        im_height = 800
    elif res == '2560':
        im_height = 533
    elif res == '1920':
        im_height = 400
    
    r_x0 = (x_0-x_up(H_old))/(im_height-x_up(H_old))
    x_new = x_up(H_new)+r_x0*(im_height-x_up(H_new))
    r_y0 = y_0/y_right(H_old)
    y_new = r_y0*y_right(H_new)
    return (int(np.floor(x_new)), int(np.ceil(y_new)))
    
def getChampBar(name, type, res, time = None):
    editDirector('render', {'interfaceAll': True})
    editDirector('render', {'selectionName': name})

    # max_attempts = 3
    # for i in range(max_attempts):
        # try: 
    sleep(0.1)
    multipliers = {'1920': 2, '3840': 4, '960': 0.5, '2560': 2.6667}
    add_y = {'1920': 1, '3840': 2, '2560': 1}
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
        bar_empty = empty_mask[y+add_y[res], x+w:]
    else:
        bar_empty = empty_mask[y+add_y[res], x+w:]
    bar_empty_length = np.where(bar_empty == 0)[0].min()-1
    bar_percent = bar_length/(bar_length+bar_empty_length)
    editDirector('render', {'interfaceAll': False})
        # except Exception as e:
        #     print(e)
        #     continue

    return bar_percent

def getChampIcon(champ_name):
    # Get the latest version
    versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    latest_version = requests.get(versions_url).json()[0]

    # Get champion data
    champions_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion.json"
    champions_data = requests.get(champions_url).json()["data"]    
    icon_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/img/champion/{champ_name}.png"
    return np.array(Image.open(requests.get(icon_url, stream=True).raw))


def getHUDScale(name, champ_name, res = '1920'):
    editDirector('render', {'interfaceAll': True})
    editDirector('render', {'selectionName': name})
    sleep(0.1)
    multipliers = {'1920': 2, '3840': 4, '960': 0.5, '2560': 2.6667}
    hud_offset = {'1920': 0, '2560': 0, '3840': 1}
    champ_icon = getChampIcon(champ_name)
    im = np.array(IP.getScreenshot(None, res))[-int(200*multipliers[res]):,:int(250*multipliers[res])]
    if res == '1920': # THIS IS WRONG NEEDS TO BE CHANGED WHEN 1K SCREEN IS AVAILABLE
        x0, y0 = 248, 155
        x1, y1 = 257, 164
    elif res == '2560':
        x0, y0 = 330, 10
        x1, y1 = 381, 61
    elif res == '3840':
        x0, y0 = 494, 16
        x1, y1 = 570, 92
    similarities = []
    for H in range(101):
        x0_new, y0_new = mapHUD(H, x0, y0, res)
        x1_new, y1_new = mapHUD(H, x1, y1, res)
        # downsample the icon
        champ_icon_ds = cv2.resize(champ_icon, (y1_new-y0_new, x1_new-x0_new))
        similarities.append(np.mean(np.abs(champ_icon_ds-im[x0_new:x1_new,y0_new:y1_new])))

    return similarities, np.argmin(similarities)-(hud_offset[res] if np.argmin(similarities) != 0 else 0)-(1 if res == '2560' and np.argmin(similarities) <= 41 else 0)

def getSummonerSpellIcon(icon_name):
    # Get the latest version
    versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    latest_version = requests.get(versions_url).json()[0]
    icon_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/img/spell/{icon_name}.png"
    return np.array(Image.open(requests.get(icon_url, stream=True).raw))


def getSummonerSpellCD(names, summoner_spells,threshold = 0.17, res = '1920', HUD = 0):
    out_cds = {name: [] for name in names}
    for name in names:
        editDirector('render', {'interfaceAll': True})
        editDirector('render', {'selectionName': name})
        sleep(0.1)
        multipliers = {'1920': 2, '3840': 4, '960': 0.5, '2560': 2.6667}
        im = np.array(IP.getScreenshot(None, res))[-int(200*multipliers[res]):,:int(250*multipliers[res])]
        if res == '3840':
            x0, y0 = 587, 290
            x1, y1 = 629+1, 332+1
            x2, y2 = 587, 336
            x3, y3 = 629+1, 378+1
        elif res == '2560':
            x0, y0 = 391, 193
            x1, y1 = 419+1, 221+1
            x2, y2 = 391, 224
            x3, y3 = 419+1, 252+1
        x0, y0 = mapHUD(HUD, x0, y0, res)
        x1, y1 = mapHUD(HUD, x1, y1, res)
        x2, y2 = mapHUD(HUD, x2, y2, res)
        x3, y3 = mapHUD(HUD, x3, y3, res)
        summoner1_curr = im[x0:x1,y0:y1]
        summoner2_curr = im[x2:x3,y2:y3]
        summoner1, summoner2 = summoner_spells[name][0], summoner_spells[name][1]
        summoner1_icon = getSummonerSpellIcon(summoner1)
        summoner2_icon = getSummonerSpellIcon(summoner2)
        sim1 = np.mean(np.abs(cv2.resize(summoner1_icon, (summoner1_curr.shape[1], summoner1_curr.shape[0])).astype(float)-summoner1_curr.astype(float)))/255
        sim2 = np.mean(np.abs(cv2.resize(summoner2_icon, (summoner2_curr.shape[1], summoner2_curr.shape[0])).astype(float)-summoner2_curr.astype(float)))/255 

        out_cds[name].append([sim1<threshold, sim2<threshold])
    return out_cds

# Old implementation with easyOCR
# def getSummonerSpellCD(names, res = '1920', HUD = 0):
#     out_cds = {name: [] for name in names}
#     for name in names:
#         editDirector('render', {'interfaceAll': True})
#         editDirector('render', {'selectionName': name})
#         sleep(0.1)
#         multipliers = {'1920': 2, '3840': 4, '960': 0.5, '2560': 2.6667}
#         im = np.array(IP.getScreenshot(None, res))[-int(200*multipliers[res]):,:int(250*multipliers[res])]
#         if res == '3840':
#             x0, y0 = 587, 290
#             x1, y1 = 629+1, 332+1
#             x2, y2 = 587, 336
#             x3, y3 = 629+1, 378+1
#         elif res == '2560':
#             x0, y0 = 391, 193
#             x1, y1 = 419+1, 221+1
#             x2, y2 = 391, 224
#             x3, y3 = 419+1, 252+1
#         x0, y0 = mapHUD(HUD, x0, y0, res)
#         x1, y1 = mapHUD(HUD, x1, y1, res)
#         x2, y2 = mapHUD(HUD, x2, y2, res)
#         x3, y3 = mapHUD(HUD, x3, y3, res)
#         summoner1 = im[x0:x1,y0:y1]
#         summoner2 = im[x2:x3,y2:y3]
#         reader = easyocr.Reader(['en'])
#         results1 = reader.readtext(summoner1, allowlist = '0123456789', text_threshold = 0.4, low_text = 0.3, link_threshold = 0.2)
#         results2 = reader.readtext(summoner2, allowlist = '0123456789', text_threshold = 0.4, low_text = 0.2, link_threshold = 0.2)
#         if len(results1) == 0:
#             out_cds[name].append(0)
#         else:
#             out_cds[name].append(results1[np.array(list(map(lambda x: x[1:],results1)))[:,1].argmax()][1])
#         if len(results2) == 0:
#             out_cds[name].append(0)
#         else:
#             out_cds[name].append(results2[np.array(list(map(lambda x: x[1:],results2)))[:,1].argmax()][1])
#     return out_cds

ult_scores = {
    'aatrox': 2,
    'ahri': 3,
    'akali': 2,
    'akshan': 1,
    'alistar': 2,
    'ambessa': 2,
    'amumu': 3,
    'anivia': 0,
    'annie': 3,
    'aphelios': 1.5,
    'ashe': 2.5,  # Fixed from incorrect aurelionsolr.png
    'aurelionsol': 2,
    'aurora': 3,
    'azir': 2,
    'bard': 1, #
    'belveth': 0, #
    'blitzcrank': 2,
    'brand': 2,
    'braum': 2.5,
    'briar': 1.5,
    'caitlyn': 1,
    'camille': 2,
    'cassiopeia': 3,
    'chogath': 3,
    'corki': 0, #
    'darius': 3,
    'diana': 2,
    'draven': 2,
    'drmundo': 2.5,
    'ekko': 3,
    'elise': 0, #
    'evelynn': 3,
    'ezreal': 1,
    'fiddlesticks': 1.5, #
    'fiora': 3,
    'fizz': 3,
    'galio': 0, #
    'gangplank': 1.5,
    'garen': 3,
    'gnar': 1.5,
    'gragas': 1.5,
    'graves': 1.5,
    'gwen': 2.5,
    'hecarim': 2,
    'heimerdinger': 3,
    'hwei': 1.5,
    'illaoi': 3,
    'irelia': 2,
    'ivern': 3,
    'janna': 0.5, #?
    'jarvaniv': 2,
    'jax': 1.5,
    'jayce': 0, #
    'jhin': 1, #?
    'jinx': 2, 
    'kaisa': 2.5,
    'kalista': 0, #
    'karma': 0, #
    'karthus': 1, #
    'kassadin': 0, #
    'katarina': 3,
    'kayle': 3,
    'kayn': 2,
    'kennen': 3,
    'khazix': 2,
    'kindred': 1.5,
    'kled': 1,
    'kogmaw': 0, #
    'ksante': 3,
    'leblanc': 1.5, #
    'leesin': 2,
    'leona': 3,
    'lillia': 3,
    'lissandra': 3,
    'lucian': 2,
    'lulu': 2,
    'lux': 2,
    'malphite': 3,
    'malzahar': 3,
    'maokai': 3,
    'masteryi': 3,
    'mel': 2,
    'milio': 1,
    'missfortune': 2,
    'mordekaiser': 3,
    'morgana': 2,
    'naafiri': 3,
    'nami': 1.5,
    'nasus': 3,
    'nautilus': 3,
    'neeko': 2.5,
    'nidalee': 0, #
    'nilah': 3,
    'nocturne': 3,
    'nunu': 2,
    'olaf': 3,
    'orianna': 2,
    'ornn': 3,
    'pantheon': 1,
    'poppy': 2,
    'pyke': 3,
    'qiyana': 3,
    'quinn': 0, #
    'rakan': 3,
    'rammus': 1,
    'reksai': 2,
    'rell': 2.5,
    'renata': 3,
    'renekton': 3,
    'rengar': 2,
    'riven': 3,
    'rumble': 2,
    'ryze': 0, #
    'samira': 0, #
    'sejuani': 2.5,
    'senna': 1.5,
    'seraphine': 3,
    'sett': 2,
    'shaco': 1,
    'shen': 0, #
    'shyvana': 3,
    'singed': 2,
    'sion': 3,
    'sivir': 2,
    'skarner': 2,
    'smolder': 2,
    'sona': 3,
    'soraka': 3,
    'swain': 3,
    'sylas': 2, # how do we do this?
    'syndra': 3,
    'tahmkench': 2,
    'taliyah': 0, #
    'talon': 3,
    'taric': 3,
    'teemo': 0,
    'thresh': 2,
    'tristana': 1.5,
    'trundle': 2,
    'tryndamere': 3,
    'twistedfate': 0, #
    'twitch': 2,
    'udyr': 0, #
    'urgot': 2,
    'varus': 3,
    'vayne': 2,
    'veigar': 2.5,
    'velkoz': 2.5,
    'vex': 2,
    'vi': 3,
    'viego': 3,
    'viktor': 2,
    'vladimir': 1,
    'volibear': 2,
    'warwick': 3,
    'wukong': 3,
    'xayah': 3,
    'xerath': 1,
    'xinzhao': 2,
    'yasuo': 1.5,
    'yone': 2,
    'yorick': 2,
    'yuumi': 3,
    'zac': 1.5,
    'zed': 3,
    'zeri': 2,
    'ziggs': 1,
    'zilean': 2,  # Fixed from incorrect zyrar.png
    'zoe': 0,
    'zyra': 2
}


# Add this dictionary near the top of the file with other constants
ult_icon_names = {
    'aatrox': ['aatrox_r.png'],
    'ahri': ['icons_ahri_r.png'],
    'akali': ['akali_r.png', 'akali_r2.png'],
    'akshan': ['akshan_r.png'],
    'alistar': ['alistar_r.png'],
    'ambessa': ['icon_ambessa_r.domina.png'],
    'amumu': ['amumu_r.png'],
    'anivia': ['anivia_r.png'],
    'annie': ['annie_r1.png'],
    'aphelios': ['apheliosr.png'],
    'ashe': ['ashe_r.png'],  # Fixed from incorrect aurelionsolr.png
    'aurelionsol': ['aurelionsolr.png', 'aurelionsolr1.png', 'aurelionsolr2.png'],
    'aurora': ['aurorar.png'],
    'azir': ['azir_r.png'],
    'bard': ['bard_r.png'], #
    'belveth': ['belvethr.png'], #
    'blitzcrank': ['blitzcrankr.png'],
    'brand': ['brandr.png'],
    'braum': ['braum_r.png'],
    'briar': ['briarr.png'],
    'caitlyn': ['caitlynr.png'],
    'camille': ['camille_r.png'],
    'cassiopeia': ['cassiopeia_r.png'],
    'chogath': ['greenterror_feast.png'],
    'corki': ['corki_missilebarrage.png', 'corki_r_bigone.png'], #
    'darius': ['darius_icon_sudden_death.png'],
    'diana': ['diana_r_moonfall.png'],
    'draven': ['draven_whirlingdeath.png'],
    'drmundo': ['drmundo_r.png'],
    'ekko': ['ekko_r.png'],
    'elise': ['eliser.png'], #
    'evelynn': ['evelynn_r.png'],
    'ezreal': ['ezreal_r.png'],
    'fiddlesticks': ['fiddlesticksr.png'], #
    'fiora': ['fiora_r.png'],
    'fizz': ['fizz_r.png'],
    'galio': ['galio_r.png'], #
    'gangplank': ['gangplank_r.png'],
    'garen': ['garen_r.png'],
    'gnar': ['gnarbig_r.png', 'gnar_r_grey.png'],
    'gragas': ['gragasexplosivecask.png'],
    'graves': ['graveshighnoon.png'],
    'gwen': ['gwen_r.png', 'gwen_r2.png', 'gwen_r3.png'],
    'hecarim': ['hecarim_onslaughtofshadows.png'],
    'heimerdinger': ['heimerdinger_r.png'],
    'hwei': ['hweir.png'],
    'illaoi': ['illaoi_r.png'],
    'irelia': ['irelia_r.png'],
    'ivern': ['ivern_r.png'],
    'janna': ['jannar.png'], #?
    'jarvaniv': ['jarvanivr.png'],
    'jax': ['jaxr.png'],
    'jayce': ['jaycer_melee.png', 'jaycer_r.png'], #
    'jhin': ['jhin_r.png'], #?
    'jinx': ['jinx_r.png'], 
    'kaisa': ['kaisa_r.png'],
    'kalista': ['kalista_r.png'], #
    'karma': ['karma_r.png'], #
    'karthus': ['karthus_r.png'], #
    'kassadin': ['kassadin_r.png'], #
    'katarina': ['katarina_r.png'],
    'kayle': ['kayle_r.png'],
    'kayn': ['kayn_r1_disabled.png', 'kayn_r1_primary.png'],
    'kennen': ['kennen_r.png'],
    'khazix': ['khazix_r.png'],
    'kindred': ['kindred_r.png'],
    'kled': ['kled_r.png'],
    'kogmaw': ['kogmaw_livingartillery.png'], #
    'ksante': ['icons_ksante_r1.png'],
    'leblanc': ['leblancr.png', 'leblancre.png', 'leblancrq.png', 'leblancrr.png', 'leblancrw.png'], #
    'leesin': ['leesinr.png'],
    'leona': ['leonar.png'],
    'lillia': ['lillia_icon_r.png'],
    'lissandra': ['lissandra_r.png'],
    'lucian': ['lucian_r.png'],
    'lulu': ['lulu_giantgrowth.png'],
    'lux': ['luxfinalfunkeln.png'],
    'malphite': ['malphite_r.png'],
    'malzahar': ['malzahar_r.png'],
    'maokai': ['maokai_r.png'],
    'masteryi': ['masteryi_r.png'],
    'mel': ['mel_r.png'],
    'milio': ['milio_r.png'],
    'missfortune': ['missfortune_r.png'],
    'mordekaiser': ['mordekaiserr.png'],
    'morgana': ['fallenangel_purgatory.png'],
    'naafiri': ['icons_naafiri_r.png'],
    'nami': ['namir.png'],
    'nasus': ['nasus_r.png'],
    'nautilus': ['nautilus_grandline.png'],
    'neeko': ['neeko_r.png'],
    'nidalee': ['nidalee_r1.png', 'nidalee_r2.png'], #
    'nilah': ['nilahr.png'],
    'nocturne': ['nocturne_paranoia.png'],
    'nunu': ['nunu_r.png'],
    'olaf': ['olafr.png'],
    'orianna': ['oriannar.png'],
    'ornn': ['ornnr1.png'],
    'pantheon': ['pantheon_r.png'],
    'poppy': ['poppy_r.png'],
    'pyke': ['pyker.png'],
    'qiyana': ['qiyana_r.png'],
    'quinn': ['quinn_r1.png', 'quinn_r2.png'], #
    'rakan': ['rakan_r.png'],
    'rammus': ['armordillo_recklesscharge.png'],
    'reksai': ['reksai_r.png'],
    'rell': ['rellr.png'],
    'renata': ['renata_r.png'],
    'renekton': ['renekton_r.png'],
    'rengar': ['rengar_r.png'],
    'riven': ['rivenbladeoftheexile.png', 'rivenwindscar.png'],
    'rumble': ['rumble_r.png'],
    'ryze': ['ryze_r.png'], #
    'samira': ['samirar8.png'], #
    'sejuani': ['sejuani_r.png'],
    'senna': ['senna_r.png'],
    'seraphine': ['seraphine_r.png'],
    'sett': ['sett_r.png'],
    'shaco': ['jester_hallucinogenbomb.png', 'jester_hallucinogenbomb_r.png'],
    'shen': ['shen_r.png'], #
    'shyvana': ['shyvanadragonsdescent.png'],
    'singed': ['singed_r.png'],
    'sion': ['sion_r1.png'],
    'sivir': ['sivir_r.png'],
    'skarner': ['skarner_r.png'],
    'smolder': ['icons_smolder_r.png'],
    'sona': ['sona_r.png'],
    'soraka': ['soraka_r.png'],
    'swain': ['swain_r.png'],
    'sylas': ['sylasr.png'], # how do we do this?
    'syndra': ['syndra_r1.png', 'syndra_r2.png'],
    'tahmkench': ['tahmkenchrwrapper.png'],
    'taliyah': ['taliyah_r.png'], #
    'talon': ['talonr.png'],
    'taric': ['taric_r.png'],
    'teemo': ['teemo_r.png'],
    'thresh': ['thresh_r.png'],
    'tristana': ['tristana_r.png'],
    'trundle': ['trundle_r.png'],
    'tryndamere': ['tryndamere_r.png'],
    'twistedfate': ['destiny_temp.png'], #
    'twitch': ['twitch_r.png'],
    'udyr': ['udyr_r.png'], #
    'urgot': ['urgot_r.png'],
    'varus': ['varusr.png'],
    'vayne': ['vayne_r.png'],
    'veigar': ['veigarprimordialburst.png'],
    'velkoz': ['velkoz_r.png'],
    'vex': ['icons_vex_r01.png'],
    'vi': ['vir.png'],
    'viego': ['viego_r.png'],
    'viktor': ['viktor_r1.viktorvgu.png', 'viktor_r2.viktorvgu.png'],
    'vladimir': ['vladimirr.png'],
    'volibear': ['volibear_icon_r.png'],
    'warwick': ['warwickr.png'],
    'wukong': ['monkeykingcyclone.png'],
    'xayah': ['xayahr.png'],
    'xerath': ['xerath_r1.png'],
    'xinzhao': ['xinzhao_r.png'],
    'yasuo': ['yasuo_r_grey.png'],
    'yone': ['yoner.png'],
    'yorick': ['yorick_r.png', 'yorick_r2.png'],
    'yuumi': ['yuumir.png'],
    'zac': ['zacr.png'],
    'zed': ['zedr.png'],
    'zeri': ['zerir.png'],
    'ziggs': ['ziggsr.png'],
    'zilean': ['zilean_r.png'],  # Fixed from incorrect zyrar.png
    'zoe': ['zoe_r.png'],
    'zyra': ['zyra_r.png']
}

def getChampUltIcon(champ_name):
    """Get champion ultimate ability icon from communitydragon"""
    # Handle special character names
    if champ_name == "Bel'Veth":
        champ_name = "Belveth"
    elif champ_name == "Kai'Sa":
        champ_name = "Kaisa"
    elif champ_name == "Kha'Zix":
        champ_name = "Khazix"
    elif champ_name == "Rek'Sai":
        champ_name = "RekSai"
    elif champ_name == "Wukong":
        champ_name = "MonkeyKing"
    
    # Convert to lowercase and remove special chars
    champ_name = ''.join(c.lower() for c in champ_name if c.isalnum())
    
    # Get the icon filename
    if champ_name in ult_icon_names:
        icon_name = ult_icon_names[champ_name]
        # If multiple icons exist, use the first one
        if isinstance(icon_name, list):
            icon_name = icon_name[0]
    else:
        # Default pattern
        icon_name = f"{champ_name}_r.png"
    
    url = f"https://raw.communitydragon.org/latest/game/assets/characters/{champ_name}/hud/icons2d/{icon_name}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        return np.array(img)
    except:
        print(f"Failed to get ult icon for {champ_name}")
        return None

def getUltCD(names, champ_names, res = '1920', HUD = 0, threshold = 0.17):
    """Check if champions have ultimate ability available"""
    out_cds = {name: False for name in names}  # False means ult on cooldown
    
    for i, name in enumerate(names):
        editDirector('render', {'interfaceAll': True})
        editDirector('render', {'selectionName': name})
        sleep(0.1)
        
        # Get screenshot
        multipliers = {'1920': 2, '3840': 4, '960': 0.5, '2560': 2.6667}
        im = np.array(IP.getScreenshot(None, res))[-int(200*multipliers[res]):,:int(250*multipliers[res])]
        
        # Get coordinates based on resolution
        if res == '2560':
            x0, y0 = 391, 150
            x1, y1 = 419+1, 177+1
        # Add other resolutions as needed
        
        # Map HUD coordinates
        x0, y0 = mapHUD(HUD, x0, y0, res)
        x1, y1 = mapHUD(HUD, x1, y1, res)
        
        # Get the ult icon from screenshot
        ult_icon = im[x0:x1, y0:y1]
        
        # Get reference ult icon
        ref_ult = getChampUltIcon(champ_names[i])
        if ref_ult is None:
            continue
            
        # Convert reference icon to RGB if it has alpha channel
        if ref_ult.shape[-1] == 4:
            ref_ult = ref_ult[:,:,:3]
            
        # Resize reference to match game icon size
        ref_ult = cv2.resize(ref_ult, (ult_icon.shape[1], ult_icon.shape[0]))
        
        # Calculate similarity
        similarity = np.mean(np.abs(ult_icon.astype(float) - ref_ult.astype(float))) / 255
        
        # If similarity is high enough, ult is available
        out_cds[name] = similarity < threshold

    return out_cds


def getRecall(name, res = '1920', HUD = 0, threshold = 0.3):
    editDirector('render', {'interfaceAll': True})
    editDirector('render', {'selectionName': name})
    recall_icon = np.array(Image.open(requests.get('https://raw.communitydragon.org/latest/game/data/images/ui/teleporthome.png', stream=True).raw))
    multipliers = {'1920': 2, '3840': 4, '960': 0.5, '2560': 2.6667}
    im = np.array(IP.getScreenshot(None, res))[-int(200*multipliers[res]):,:int(250*multipliers[res])]
    if res == '3840':
        x0, y0 = 435, 1
        x1, y1 = 465+1, 31+1
        x0_up, y0_up = 402, 1
        x1_up, y1_up = 432+1, 31+1
        icon_length = y1-y0-1
        long_icon_offset = 7
        short_icon_offset = 3
        in_icon_x_offset_up = 3
        in_icon_y_offset_left = 2
        in_icon_y_offset_right = 4
        in_icon_x_offset_down = 3
    for i in range(5):  
        y0_final = y0 + in_icon_y_offset_left
        y1_final = y1 - in_icon_y_offset_right
        y0_up_final = y0_up + in_icon_y_offset_left
        y1_up_final = y1_up - in_icon_y_offset_right
        x0_final = x0 + in_icon_x_offset_up
        x1_final = x1 - in_icon_x_offset_down
        x0_up_final = x0_up + in_icon_x_offset_up
        x1_up_final = x1_up - in_icon_x_offset_down
        
        x0_new, y0_new = mapHUD(HUD, x0_final, y0_final, res)
        x1_new, y1_new = mapHUD(HUD, x1_final, y1_final, res)
        x0_up_new, y0_up_new = mapHUD(HUD, x0_up_final, y0_up_final, res)
        x1_up_new, y1_up_new = mapHUD(HUD, x1_up_final, y1_up_final, res)
        current_icon = im[x0_new:x1_new,y0_new:y1_new]
        current_icon_up = im[x0_up_new:x1_up_new,y0_up_new:y1_up_new]

        sim = np.mean(np.abs(current_icon-cv2.resize(recall_icon, (current_icon.shape[1], current_icon.shape[0]))[:,:,:-1]))/255
        sim_up = np.mean(np.abs(current_icon_up-cv2.resize(recall_icon, (current_icon_up.shape[1], current_icon_up.shape[0]))[:,:,:-1]))/255
        if sim < threshold or sim_up < threshold:
            return True
        y0 += icon_length+short_icon_offset
        y1 += icon_length+short_icon_offset
        y0_up += icon_length+short_icon_offset
        y1_up += icon_length+short_icon_offset
    return False


def isLongIcon(icon, threshold = 0.8):
    smite_icon = np.array(Image.open(requests.get('https://raw.communitydragon.org/latest/game/data/images/ui/smite.png', stream=True).raw))
    gold_quest_progress_icon = np.array(Image.open(requests.get('https://raw.communitydragon.org/latest/game/data/images/ui/goldquestprogress.png', stream=True).raw))
    # take the top half of each icon
    smite_icon = smite_icon[:smite_icon.shape[0]//2,:]
    gold_quest_progress_icon = gold_quest_progress_icon[:gold_quest_progress_icon.shape[0]//2,:]
    smite_icon = cv2.resize(smite_icon, (icon.shape[1], icon.shape[0]))
    gold_quest_progress_icon = cv2.resize(gold_quest_progress_icon, (icon.shape[1], icon.shape[0]))
    return np.mean(np.abs(icon-smite_icon)) > threshold or np.mean(np.abs(icon-gold_quest_progress_icon)) > threshold

def changeTime(time, delay):
    editDirector('playback', {'time': time-delay, 'paused': False, 'speed': 2})
    sleep(delay/2)
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
    Ms = {'1920': 30, '3840': 60, '2560': 40}
    min_sampless = {'1920': 50, '3840': 100, '2560': 75}
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
        Ms = {'1920': 30, '3840': 60, '2560': 40}
        min_sampless = {'1920': 50, '3840': 100, '2560': 75}
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

def closeReplay():
    app_name = "League of Legends.exe"
    for process in psutil.process_iter(['pid', 'name']):
        try:
            # Check if the process name matches
            if process.info['name'] == app_name:
                print(f"Closing {app_name} (PID: {process.info['pid']})")
                process.terminate()  # Gracefully terminate the process
                process.wait()       # Wait for the process to exit
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

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
        start_time = time.time()
        time_lim = 20 # seconds
        while True:
            line = file.readline()
            if not line:
                sleep(1)  # Wait for new data
            # Check for specific log entries that indicate the replay is loading
            if "Pop: LoadingScreen complete" in line or time.time() - start_time > time_lim:
                print("Replay has finished loading.")
                sleep(5)
                break
            # else:
                # print("Replay is still loading...")