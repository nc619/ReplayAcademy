import requests
import math
import json
import os
import replay_utils as RU
import numpy as np
from tkinter import Tk, filedialog
from tqdm import tqdm
from time import sleep


api_key = "RGAPI-606ef5aa-a9be-4c2c-9e92-fcf858b97492"
versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
latest_version = requests.get(versions_url).json()[0]
items_data = requests.get(f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/item.json").json()["data"]
api_url = "https://127.0.0.1:2999/replay"

with open("champ_scores.json","r") as file:
    champ_scores_global = json.load(file) 
with open("matchup_difficulty_data.json","r") as file:
    champ_scores_relative = json.load(file) 


def getSummonerSpellKeys():
    versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    latest_version = requests.get(versions_url).json()[0]
    summoner_spell_data = requests.get(f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/summoner.json").json()["data"]
    summoner_spell_keys = {int(summoner_spell_data[key]['key']): key for key in summoner_spell_data}
    return summoner_spell_keys


def getReplayData(match_id,time, summoner_names, champ_names, summs,ids, res):
    replay_time = np.round(time/1000,2)
    match_id = match_id.split("_")[1]
    RU.changeTime(replay_time, 3.6)
    champ_dict = RU.getChampStatus(summoner_names, res = res)
    _, HUD_scale = RU.getHUDScale(summoner_names[0], champ_names[0], res = res)

    cds = RU.getSummonerSpellCD(summoner_names, res = res, HUD = HUD_scale, summoner_spells = summs)
    ult_cds = RU.getUltCD(summoner_names, champ_names, res = res, HUD = HUD_scale)
    champ_dict = {ids[i]: champ_dict[name] for i, name in enumerate(summoner_names)}
    cds = {ids[i]: cds[name] for i, name in enumerate(summoner_names)}
    ult_cds = {ids[i]: ult_cds[name] for i, name in enumerate(summoner_names)}
    return champ_dict, cds, ult_cds

def stats_calculator(champ, level):
    cur_path = os.getcwd()
    versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    latest_version = requests.get(versions_url).json()[0]

    # Get champion data
    champions_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion.json"
    champions_data = requests.get(champions_url).json()["data"]    
    champ_data_path = os.path.join(cur_path, 'assets', 'dragontail-14.16.1', '14.16.1', 'data', 'en_GB','champion')
    path = os.path.join(champ_data_path, champ + '.json')
    with open(path,"r",  encoding='utf-8') as file:
        data = json.load(file) 
    stats = data["data"][champ]["stats"]
    stats_list = []
    stats_list.append(stats["hp"] + stats["hpperlevel"] * (level-1) * (0.7025 + 0.0175 * (level-1)))
    stats_list.append(stats["mp"] + stats["mpperlevel"] * (level-1) * (0.7025 + 0.0175 * (level-1)))
    stats_list.append(stats["armor"] + stats["armorperlevel"] * (level-1) * (0.7025 + 0.0175 * (level-1)))
    stats_list.append(stats["spellblock"] + stats["spellblockperlevel"] * (level-1) * (0.7025 + 0.0175 * (level-1)))
    stats_list.append(stats["hpregen"] + stats["hpregenperlevel"] * (level-1) * (0.7025 + 0.0175 * (level-1)))
    stats_list.append(stats["mpregen"] + stats["mpregenperlevel"] * (level-1) * (0.7025 + 0.0175 * (level-1)))
    stats_list.append(stats["attackdamage"] + stats["attackdamageperlevel"] * (level-1) * (0.7025 + 0.0175 * (level-1)))
    stats_list.append(stats["attackspeed"] + stats["attackspeedperlevel"] * (level-1) * (0.7025 + 0.0175 * (level-1)))
    total_worth = 0
    total_worth += stats_list[0] * 2.76
    total_worth += stats_list[1] * 1
    total_worth += stats_list[2] * 20
    total_worth += stats_list[3] * 20
    total_worth += stats_list[4] * 3
    total_worth += stats_list[5] * 4
    total_worth += stats_list[6] * 35
    total_worth += stats_list[7] * 25
    return total_worth

def level_diff_cal(level1,level2):
    level1_scaled = 600 * (level1-1) * (0.7025 + 0.0175 * (level1-1))
    level2_scaled = 600 * (level2-1) * (0.7025 + 0.0175 * (level2-1))
    return level1_scaled - level2_scaled


def nico_data(matches, res):
    result = {}
    count_total = 0
    labels = []
    time1 = 70000
    time2 = 900000
    summoner_spell_keys = getSummonerSpellKeys()
    print(summoner_spell_keys)
    for match in tqdm(matches, "Matches"):
        try:
            count_match = 0
            url = "https://" + "europe" + ".api.riotgames.com/lol/match/v5/matches/" + match
            header = {"X-Riot-Token": api_key}
            resp= requests.get(url, headers = header)
            stat = resp.status_code
            if stat != 200:
                print("Skipping match: ", match)
                continue
            match_info = resp.json()
            champs = []
            names = []
            summs = {}
            for participant in match_info["info"]["participants"]:
                champs.append(participant["championName"])
                names.append(participant["riotIdGameName"])
                summs[names[-1]] = [summoner_spell_keys[participant["summoner1Id"]], summoner_spell_keys[participant["summoner2Id"]]]



            url = "https://" + "europe" + ".api.riotgames.com/lol/match/v5/matches/" + match + "/timeline"
            header = {"X-Riot-Token": api_key}
            resp= requests.get(url, headers = header)
            stat = resp.status_code
            if stat != 200:
                print("Skipping match: ", match)
                continue
            match_timeline = resp.json()
            
            
            events = []
            timestamp = 0
            frames = match_timeline["info"]["frames"]
            min1 = time1//60000
            min2 = int(math.ceil(time2/60000))

            levels = [0,0,0,0,0,0,0,0,0,0]
            gold_accum = [0,0,0,0,0,0,0,0,0,0]
            initial = frames[min1 - 1]["participantFrames"]
            idex = 0
            for id, part in initial.items():
                gold_accum[idex] = part["totalGold"] - part["currentGold"]  
                levels[idex] = part["level"]
                idex +=1



            for i in range(min1, min2 + 1):
                for event in tqdm(frames[i]["events"], "Events"):
                    valid_event= 0
                    if time1 < event["timestamp"] < time2:
                        if ("participantId" in event.keys() and event["participantId"] == 6) and "ITEM" in event["type"]:
                            pass
                        if event["type"] == "ITEM_PURCHASED":
                            item = str(event["itemId"])
                            id = event["participantId"]
                            gold = items_data[item]["gold"]["total"]
                            gold_accum [id -1] += gold
                        elif event["type"] == "ITEM_DESTROYED":
                            item = str(event["itemId"])
                            id = event["participantId"]
                            gold = items_data[item]["gold"]["total"]
                            gold_accum [id -1] -= gold
                        elif event["type"] == "ITEM_UNDO":
                            item = str(event["beforeId"])
                            id = event["participantId"]
                            gold = event["goldGain"]
                            gold_accum [id -1] -= gold
                        elif event["type"] == "LEVEL_UP":
                            id = event["participantId"]
                            level = event["level"]
                            levels[id - 1] = level
                        elif event["type"] == "CHAMPION_KILL":
                            timestamp = event["timestamp"]
                            position = event["position"]
                            killerid= event["killerId"]
                            victimid = event["victimId"]
                            killer = champs[killerid - 1]
                            victim = champs[victimid - 1]
                            killer_gold = gold_accum[killerid -1]
                            victim_gold = gold_accum[victimid -1]
                            killer_level = levels[killerid - 1]
                            victim_level = levels[victimid - 1]
                            #killer_stats = last_buy[killerid - 1]["championStats"]
                            #victim_stats = last_buy[victimid - 1]["championStats"]
                            lane = "none"
                            valid_event= 0
                            if "assistingParticipantIds" not in event:
                                #Solo kills only for top, mid, jgl(jgl for now)
                                if (killerid == 1 or killerid == 6) and (victimid == 1 or victimid == 6):
                                    lane = "top"
                                    valid_event= 1
                                if (killerid == 2 or killerid == 7) and (victimid == 2 or victimid == 7):
                                    lane = "jungle"
                                    valid_event= 1
                                if (killerid == 3 or killerid == 8) and (victimid == 3 or victimid == 8):
                                    lane = "mid"
                                    valid_event= 1
                            if (killerid == 4 or killerid == 4 or killerid == 9 or killerid == 10) and (victimid == 4 or victimid == 5 or victimid == 9 or victimid == 10):
                                lane = "adc"
                                valid_event= 0
                            
                            if valid_event == 1 and lane != "none" and killer.lower() in champ_scores_relative[lane] and victim.lower() in champ_scores_relative[lane][killer.lower()]:
                                valid_event = 1
                                same_lane_flag = 1
                                print("valid matchup: " ,killer, victim)
                            elif valid_event == 1 and lane == "none":# and lane != "none": 
                                valid_event = 1
                                same_lane_flag = 0
                                # print("invalid solo kill matchup: " ,killer, victim)
                            else:
                                valid_event = 0

                            if valid_event == 1:
                                count_match += 1
                                count_total += 1
                                temp = {}
                                #killer_level_gold = stats_calculator(killer, killer_level)
                                #victim_level_gold = stats_calculator(victim, victim_level)
                                if count_match == 1:
                                    port, authorization_header = RU.getLcuCredentials()
                                    RU.openReplay(match.split("_")[1], port, authorization_header)
                                    sleep(5)
                                    RU.is_replay_loading()

                                champ_dict, cds, ult_cds = getReplayData(match,
                                                                        timestamp-25000,
                                                                        [names[killerid-1], names[victimid-1]],
                                                                        [champs[killerid-1], champs[victimid-1]],
                                                                        summs,
                                                                        [killerid, victimid],
                                                                        res)
                                level_gold_diff = level_diff_cal(killer_level,victim_level)
                                temp["match"] = match
                                temp["killer"] = killer
                                temp["victim"] = victim
                                temp["item_gold_diff"] = killer_gold - victim_gold
                                temp["level_gold_diff"] = level_gold_diff
                                temp["time"] = timestamp
                                temp["position"] = position
                                temp["lane"] = lane
                                temp["killer_id"] = killerid
                                temp["victim_id"] = victimid
                                temp["count"] = count_match
                                temp["killer_hp"] = champ_dict[killerid]["hp"]
                                temp["victim_hp"] = champ_dict[victimid]["hp"]
                                temp["killer_cds"] = cds[killerid]
                                temp["victim_cds"] = cds[victimid]
                                temp["killer_ult_cd"] = ult_cds[killerid]
                                temp["victim_ult_cd"] = ult_cds[victimid]
                                temp["killer_mana"] = champ_dict[killerid]["mana"]
                                temp["victim_mana"] = champ_dict[victimid]["mana"]
                                if same_lane_flag == 1:
                                    temp["killer_victim_score"] = champ_scores_relative[lane][killer.lower()][victim.lower()]
                                else:
                                    temp["killer_victim_score"] = champ_scores_global[lane][killer.lower()]-champ_scores_global[lane][victim.lower()]
                                temp["same_lane_flag"] = same_lane_flag
                                result[count_total] = temp
                            events.append(event)
            RU.closeReplay()
        except:
            print(f"Error in match {match}")
    print(result) 
    i = 1
    found_flag = False
    if not os.path.isdir("solo_kills_results"):
        os.makedirs("solo_kills_results")
    while not found_flag:
        if os.path.exists(f"solo_kills_results/solo_kills_results_{i}"):
            i += 1
        else:
            found_flag = True
    import pickle
    with open(f"solo_kills_results/solo_kills_results_{i}","wb") as file:
        pickle.dump(result,file)






res = '2560'
# champ_dict = RU.getChampStatus(['Fiora'], res = res)
# _, HUD_scale = RU.getHUDScale('Penetrasion', "Fiora", res = res)
# cds = RU.getSummonerSpellCD(['Fiora'], res = res, HUD = HUD_scale)
# recall = RU.getRecall('Dmonnantim', res = res, HUD = HUD_scale)

def get_replay_directory():
    root = Tk()
    root.withdraw()  # Hide the main window
    replay_dir = filedialog.askdirectory(title="Select League Replay Directory")
    root.destroy()
    return replay_dir

# replay_dir = get_replay_directory()
replay_dir = "C:/Users/Nico/Documents/League of Legends/Replays"
match_list = [a.replace("-","_").split(".rofl")[0] for a in os.listdir(replay_dir)]
print(match_list)
nico_data(match_list, res = res)
pass