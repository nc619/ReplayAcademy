#Store and process each match data

import os
import requests
import json
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

    

    def __init__(self, id, puuid, region1):
        self.match_id = id
        self.puuid = puuid
        self.region1 = region1


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

        
    def process_match(self):
        #excutes when each game is processed

        #get timeline
        self.load_match_timeline()

        #find user info (team,role,etc)
        ids = self.match_timeline["metadata"]["participants"]
        user_pos = ids.index(self.puuid) + 1
        print(user_pos)
        if user_pos > 5:
            range_value = 100
            user_oppnt= user_pos - 5
        else:
            range_value = 200
            user_oppnt = user_pos + 5

        #find and classify kill events
        kill_events = []
        all_frames = self.match_timeline["info"]["frames"]
        for frame in all_frames:
            for event in frame["events"]:
                if event["type"] == "CHAMPION_KILL":
                    if "assistingParticipantIds" in event and user_pos in event["assistingParticipantIds"]:
                        event["RA_note"] = "Kill Assist"
                        kill_events.append(event)
                    elif event["killerId"] == user_pos and "assistingParticipantIds" not in event:
                        event["RA_note"] = "Solo Kill"
                        kill_events.append(event)
                    elif event["killerId"] == user_pos and "assistingParticipantIds" in event:
                        event["RA_note"] = "Assisted Kill"
                        kill_events.append(event)
                    elif event['victimId'] == user_pos and "assistingParticipantIds" not in event:
                        event["RA_note"] = "Solo Killed"
                        kill_events.append(event)
                    elif event['victimId'] == user_pos and "assistingParticipantIds" in event:
                        event["RA_note"] = "Assisted Killed"
                        kill_events.append(event)
                    elif event["killerId"] == user_oppnt or ("assistingParticipantIds" in event and user_oppnt in event["assistingParticipantIds"]):
                        event["RA_note"] = "Oppnt takedowns"
                        kill_events.append(event)           
        with open("processing_result_temp.json","w") as file:
            json.dump(kill_events, file, indent=4)
        


        
match = Match("EUW1_6983626014", "K3NncqXpoXuEBjkd6wiNAmX4GxrPniIdIc5GMEnBiR9tQy3W5AQyh6bpZxoxtbooK9qat23qujeqBg","europe" )
match.process_match()
#with open("match_timeline.json","w") as file:
    #json.dump(match.match_timeline, file, indent=4)


