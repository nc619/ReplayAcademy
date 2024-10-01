#Store and process each match data

import os
import requests
import json
import math
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap import Style
from tkinter import messagebox
from tkinter import filedialog
from tkinter import PhotoImage

class Match():

    api_key = "RGAPI-606ef5aa-a9be-4c2c-9e92-fcf858b97492"
    match_info = {}
    match_timeline = {}
    match_id = ""
    replay_exist = 0
    RA_events = []

    

    def __init__(self, id, puuid, region1, dir):
        self.match_id = id
        self.puuid = puuid
        self.region1 = region1

        #check replay file
        self.if_replay_exist(dir)
        if self.replay_exist == 0:
            print("\nError: replay not found")
            #return

        #get timeline
        self.load_match_timeline()

        #find user pos
        ids = self.match_timeline["metadata"]["participants"]
        self.user_pos = ids.index(self.puuid) + 1


    def handle_error(self,stat, string):
            if stat == 200:
                return 1
            elif stat == 429:
                tk.messagebox.showinfo(title= string + "Error", message="Too busy, try again later")
                return 0
            elif stat == 404:
                tk.messagebox.showinfo(title=string + "Error", message="Player not found")
                return 0
            else:
                tk.messagebox.showinfo(title=string + "Error", message="Error Code: " + str(stat) )
                return 0

    def load_match_info(self):
        url = "https://" + self.region1 + ".api.riotgames.com/lol/match/v5/matches/" + self.match_id
        header = {"X-Riot-Token": self.api_key}
        resp= requests.get(url, headers = header)
        stat = resp.status_code
        if self.handle_error(stat, "load match info in class Match") == 0:
            return
        self.match_info = resp.json()
        pass

    def load_match_timeline(self):
        url = "https://" + self.region1 + ".api.riotgames.com/lol/match/v5/matches/" + self.match_id + "/timeline"
        header = {"X-Riot-Token": self.api_key}
        resp= requests.get(url, headers = header)
        stat = resp.status_code
        if self.handle_error(stat, "load timeline in class Match") == 0:
            return
        self.match_timeline = resp.json()

    def if_replay_exist(self,dir):
        game = self.match_id.replace('_', '-')
        replay_file = game + ".rofl"
        path = dir + "/" + replay_file
        if os.path.isfile(path):
            self.if_replay_exist = 1
            return 1  
        else:
            self.if_replay_exist = 0
            return 0
        
    def cut_events(self,time1,time2):
        out = []
        frames = self.match_timeline["info"]["frames"]
        min1 = time1//60000
        min2 = int(math.ceil(time2/60000))
        for i in range(min1, min2 + 1):
            for event in frames[i]["events"]:
                if time1 < event["timestamp"] < time2:
                    out.append(event)
        return out
    
    def find_events(self, events, event_type):
        #event = 0 for match time line
        out=[]
        if events == 0:
            events = []
            all_frames = self.match_timeline["info"]["frames"]
            for frame in all_frames:
                for event in frame["events"]:
                    events.append(event)

        for event in events:
            if event["type"] == event_type:
                out.append(event)
        return out
    
    def get_level(self, time):
        level = 1
        temp = self.cut_events(0,time)
        lvl_events = self.find_events(temp,"LEVEL_UP")
        for event in lvl_events:
            if event["participantId"] == self.user_pos:
                level = event["level"]
                print(level)
        return level
    
    def get_items(self,time):
        items = []
        temp = self.cut_events(0,time)
        buy_events = self.find_events(temp,"ITEM_PURCHASED")
        for event in buy_events:
            if event["participantId"] == self.user_pos:
                item = event["itemId"]
                items.append(item)
        return items


    def regular_checks(self, frame, time):
        ptcp_frame = frame["participantFrames"][str(self.user_pos)]
        total_gold = ptcp_frame["totalGold"]
        level = ptcp_frame["level"]
        cur_gold = ptcp_frame["currentGold"]
        new_event = {}
        new_event["timestamp"] = time
        new_event["type"] = "regular checks"
        if cur_gold >= 1500:
            new_event["RA_note"] = "too much gold"
            new_event["RA_type"] = 1
            self.RA_events.append(new_event)
        if level == 3:
            new_event["RA_note"] = "Reached lv 3"
            new_event["RA_type"] = 1
            self.RA_events.append(new_event)

    def process_kill_events(self,event, timestamp):
        if "assistingParticipantIds" in event and self.user_pos in event["assistingParticipantIds"]:
            event["RA_type"] = 3
            if timestamp <= 900000:
                event["RA_type"] = 1
            event["RA_note"] = "Kill Assist"
            self.RA_events.append(event)
        elif event["killerId"] == self.user_pos and "assistingParticipantIds" not in event:
            event["RA_note"] = "Solo Kill"
            event["RA_type"] = 1
            self.RA_events.append(event)
        elif event["killerId"] == self.user_pos and "assistingParticipantIds" in event:
            event["RA_type"] = 3
            if timestamp <= 900000:
                event["RA_type"] = 1
            event["RA_note"] = "Assisted Kill"
            self.RA_events.append(event)
        elif event['victimId'] == self.user_pos and "assistingParticipantIds" not in event:
            event["RA_type"] = 1
            event["RA_note"] = "Solo Killed"
            self.RA_events.append(event)
        elif event['victimId'] == self.user_pos and "assistingParticipantIds" in event:
            event["RA_type"] = 3
            if timestamp <= 900000:
                event["RA_type"] = 1
            event["RA_note"] = "Assisted Killed"
            self.RA_events.append(event)
        elif event["killerId"] == self.user_oppnt or ("assistingParticipantIds" in event and self.user_oppnt in event["assistingParticipantIds"]):
            event["RA_type"] = 3
            if timestamp <= 900000:
                event["RA_type"] = 1
            event["RA_note"] = "Oppnt takedowns"
            self.RA_events.append(event) 

    def obj_timer(self, event, timestamp):
        monster = ["eggs", "herald", "drake", "baron"]
        new_event = {}
        
        if timestamp >= self.obj_times[0] and self.obj_avaiable[0] and self.obj_said[0]:
            new_event["type"] = "objectives spawned"
            new_event["timestamp"] = self.obj_times[0]
            new_event["RA_note"] = monster[0] + "spawned"
            new_event["RA_type"] = 1
            self.obj_said[0] = 0
            self.RA_events.append(new_event)





        if "monsterType" in event and event["monsterType"] == "HORDE":
            self.obj_count[0] += 1
            if self.obj_count[0] == 3 or self.obj_count[0] == 6:
                self.obj_said[0] = 1
                self.obj_times[0] = timestamp + 240000
                event["RA_note"] = monster[0] + " killed"
                event["RA_type"] = 1
                self.RA_events.append(event)
            if self.obj_times[0] > 840000 or self.obj_count[0] == 6:
                self.obj_avaiable[0] = 0


        
    def process_match(self):
        #excutes when each game is processed
        user_pos = self.user_pos
        if user_pos > 5:
            range_value = 100
            self.user_oppnt= user_pos - 5
        else:
            range_value = 200
            self.user_oppnt = user_pos + 5

        #init
        self.RA_events = []
        self.obj_times = [300000,840000,300000,1200000] #egg, herald, drake, baron
        self.obj_said = [1,1,1,1]
        self.obj_avaiable = [1,1,1,1]
        self.obj_count = [0,0,0,0]
        timestamp = 0


        #event main loop
        all_frames = self.match_timeline["info"]["frames"]
        for frame in all_frames:
            self.regular_checks(frame, timestamp)
            for event in frame["events"]:
                timestamp = event["timestamp"]
                self.obj_timer(event, timestamp)
                if event["type"] == "CHAMPION_KILL":
                    self.process_kill_events(event, timestamp)        
        
        with open("processing_result_temp.json","w") as file:
            json.dump(self.RA_events, file, indent=4)
        


dir = "C:/Users/Razer/Documents/League of Legends/Replays"   
match = Match("EUW1_6983626014", "K3NncqXpoXuEBjkd6wiNAmX4GxrPniIdIc5GMEnBiR9tQy3W5AQyh6bpZxoxtbooK9qat23qujeqBg","europe" , dir)
match.process_match()
with open("test2.json","w") as file:
    json.dump("test2", file, indent=4)


