#Main Menu

import time
import math
from datetime import datetime, timedelta
import os
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap import Style
from tkinter import messagebox
from tkinter import filedialog
from tkinter import PhotoImage
from PIL import Image, ImageTk
import requests
import json


class Menu_Main(ttk.Frame):
    #To do: refresh button for all, kda color, special RA score 
    #Rearrange match
  

    #Done: use name fetch puuid, store info in json, if signed dont show sign in just read data, menu logic
    #mian RA() and app structure
    #browse, check dir (find .rofl), region,  make create data.json,
    #ID panel with icon, name and lv, logout
    #ranked data exceptions, rkd data panel refresh logic
    #info button, queue type and refresh when select 
    
    
    api_key = "RGAPI-606ef5aa-a9be-4c2c-9e92-fcf858b97492"
    user_puuid = "6"
    


    def __init__(self, Frame_y, flag_sign, master=None):
        #Initialise menu root frame
        self.window_y = Frame_y
        self.flag_init = 0
        self.flag_sign = flag_sign

        super().__init__(master,width=1600, height=900, bootstyle= "info")
        self.master = master
        self.pack(fill=BOTH, expand=1)

        self.style = ttk.Style()
        self.name = ttk.StringVar()
        self.tag = ttk.StringVar()
        self.dir = ttk.StringVar()
        self.cur_page = 0
        self.region = ttk.StringVar(value= "EUROPE")
        self.region2 = ttk.StringVar(value= "EUW1")
        self.rkd_type_selected = ttk.StringVar(value="All")
        self.champ_tks = [None] * 10
        self.champ_icons = [None] * 60
        self.player_buttons = [None] * 10

        if flag_sign == 1:
            self.build_main_menu()
        else:
            self.sign_in()

        

    
        self.flag_init = 1


    def build_main_menu(self):
        self.ID_panel(0)
        self.tabs()
        self.stats(0)
        self.matches(0)

    

    def sign_in(self):
        self.f_sign = ttk.Frame(master = self, border=10, relief=SUNKEN)
        self.f_sign.place(relx=0.25, rely = 0.25, relheight=0.5, relwidth=0.5)
        l1 = tk.Label(self.f_sign, text = "Please provide your Riot Game Name and the directory of your LOL replay file (usually you can find it at...) ")
        l1.pack()
        
        l2 = tk.Label(self.f_sign, text = "Name")
        l2.pack()
        e1 = tk.Entry(self.f_sign, textvariable = self.name)
        e1.pack()

        l3 = tk.Label(self.f_sign, text = "Tag")
        l3.pack()
        e2 = tk.Entry(self.f_sign, textvariable = self.tag)
        e2.pack()

        l4 = tk.Label(self.f_sign, text = "Directory")
        l4.pack()

        self.region.set("Please select a region")

        if self.flag_sign == 1:
            with open("data.json","r") as file:
                data = json.load(file)
                self.dir.set(data['dir'])
                self.region.set(data['region'])

        self.e3 = tk.Entry(self.f_sign, textvariable = self.dir)
        self.e3.pack()

        reg_ops = ["AMARICAS", "ASIA", "EUROPE"]
        self.om1 = tk.OptionMenu(self.f_sign, self.region, *reg_ops, command= None)
        self.om1.pack()

        reg_ops2 = ["BR1", "EUN1", "EUW1", "JP1", "KR", "LA1", "LA2", "NA1", "OC1","PH2", "RU","SG2", "TH2","TR1", "TW2", "VN2"]
        self.om2 = tk.OptionMenu(self.f_sign, self.region2, *reg_ops2, command= None)
        self.om2.pack()

        b1 = tk.Button(self.f_sign, text="Browse", command=self.browse)
        b1.pack()
        b2 = tk.Button(self.f_sign, text="Sign in", command=self.check_sign_in)
        b2.pack()



    def browse(self):
        self.dir.set(filedialog.askdirectory())
        self.e3.config(textvariable=self.dir)


    def check_sign_in(self):
        name = self.name.get()
        tag = self.tag.get()
        dir = self.dir.get()
        region = self.region.get()
        region2 = self.region2.get()
        if region == "Please select a region":
            messagebox.showerror("Error", "Please select a region!")
            return

        if tag[0] == "#":
            tag=tag[1:]
        url = "https://" + region + ".api.riotgames.com/riot/account/v1/accounts/by-riot-id/" + name +"/" + tag
        header = {"X-Riot-Token": self.api_key}
        resp= requests.get(url, headers = header)
        stat = resp.status_code
        if self.handle_error(stat, "Sign in") == 0:
                return
        
        resp_json = resp.json()
        self.user_puuid = resp_json["puuid"]
        with open("data.json","r") as file:
            data = json.load(file)
        data['puuid'] = self.user_puuid
        data['flag_sign'] = 1
        data['name'] = name
        data['tag'] = tag
        data['dir'] = dir
        data['region'] = region
        data['region2'] = region2

        url = "https://" + region2 + ".api.riotgames.com/lol/summoner/v4/summoners/by-puuid/" + self.user_puuid
        resp2= requests.get(url, headers = header)
        stat = resp2.status_code   
        if self.handle_error(stat, "Sign in 2") == 0:
            return
        resp2_json = resp2.json()
        data['sumid'] = resp2_json['id']
        data['accid'] = resp2_json['accountId']
        data['iconid'] = resp2_json['profileIconId']
        data['level'] = resp2_json['summonerLevel']

        with open("data.json","w") as file:
            json.dump(data,file)
            local_flag_sign = 1
        
        flag_dir = self.check_dir(dir)
        if (local_flag_sign ==1) & (flag_dir == 1):
            self.f_sign.destroy()
            self.build_main_menu()

    

    def check_dir(self, dir):
        if not os.path.exists(dir):
            messagebox.showerror("Error", "The selected directory does not exist.")
            return 0
        if not os.access(dir, os.R_OK):
            messagebox.showerror("Error", "You do not have permission to read the directory.")
            return 0
        if not any(file.endswith('.rofl') for file in os.listdir(dir)):
            messagebox.showinfo("Info", "The directory does not contain any replay files. Please select another directory.")
            return 0
        
        return 1
        
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


    def ID_panel(self, mode):
        #mode 0 = init, 1 = update
        if mode == 0:
            with open("data.json","r") as file:
                data = json.load(file)
                puuid = data['puuid']
                region2 = data['region2']
                name = data['name']
                sumid = data['sumid']
                level = data['level']
                icon = data["iconid"]
                patch = data['patch']
            url2 = "https://"+ region2 +".api.riotgames.com/lol/league/v4/entries/by-summoner/" + sumid
            header = {"X-Riot-Token": self.api_key}
            resp2= requests.get(url2, headers = header)
            stat = resp2.status_code
            if self.handle_error(stat, "ID2") == 0:
                return
            rkd_data = resp2.json()
            self.f_ID = ttk.Frame(master = self, border=10, relief=SUNKEN)
            self.f_ID.place(relx=0, rely = 0, relheight=0.2, relwidth=0.3)


        if mode == 1:
            with open("data.json","r") as file:
                data = json.load(file)
                puuid = data['puuid']
                region2 = data['region2']
                name = data['name']
                sumid = data['sumid']
                patch = data['patch']

            url = "https://" + region2 + ".api.riotgames.com/lol/summoner/v4/summoners/by-puuid/" + puuid
            header = {"X-Riot-Token": self.api_key}
            resp= requests.get(url, headers = header)
            stat = resp.status_code   
            if self.handle_error(stat, "ID1") == 0:
                return
            
            resp_json = resp.json()
            level = resp_json["summonerLevel"]
            icon = resp_json["profileIconId"]
            data['iconid'] = icon
            data['level'] = level
            with open("data.json","w") as file:
                json.dump(data,file)
            

            url2 = "https://"+ region2 +".api.riotgames.com/lol/league/v4/entries/by-summoner/" + sumid
            resp2= requests.get(url2, headers = header)
            stat = resp2.status_code
            if self.handle_error(stat, "ID2") == 0:
                return
            rkd_data = resp2.json()
            for widget in self.f_ID.winfo_children():
                widget.destroy()
        
        self.put_icon(icon,patch)

        f = ttk.Frame(self.f_ID)
        f.place(relx=0.375, rely=0, relheight=1, relwidth= 0.625)
        l_name = tk.Label(f, text = name, anchor="center", justify=tk.CENTER)
        l_name.pack(pady=0.015*self.window_y, fill = tk.X)
        l_lv = tk.Label(f, text = "lv." + str(level), anchor="center", justify=tk.CENTER)
        l_lv.pack(pady=0.01*self.window_y, fill = tk.X)
        b = ttk.Button(f, text="Log out", command=self.sign_in)
        b.place(relx=0.18,rely=0.65)
        b2 = ttk.Button(f, text="Refresh", command=self.refresh)
        b2.place(relx=0.6,rely=0.65)
        

    def refresh(self):
        self.ID_panel(1)
        self.matches(1)
        print("refreshed")   

      
    def put_icon(self,icon,patch):
        f = ttk.Frame(self.f_ID)
        f.place(relx=0, rely=0, relheight=1, relwidth= 0.375)
        icon_num  = str(icon) + ".png"
        cur_path = os.getcwd()
        icon_path = os.path.join(cur_path, 'assets', 'dragontail-' + str(patch), patch, 'img', 'profileicon', icon_num)
        self.icon_img = Image.open(icon_path)
        len = round(0.18*self.window_y)
        self.icon_small = self.icon_img.resize((len,len), Image.Resampling.LANCZOS)
        
        self.icon_tk = ImageTk.PhotoImage(self.icon_small)
        l_icon = tk.Label(f, image = self.icon_tk)
        l_icon.place(relx=0, rely=0)

    def process_rkd(self,data):
        lenth = len(data)

        if lenth == 0:
            return 0 , 0
        
        if lenth == 1:
            rkd_type = data[0]['queueType']
            if rkd_type == "RANKED_SOLO_5x5":
                return data[0], 0
            elif rkd_type == "RANKED_FLEX_SR":
                return 0, data[0]
            else:
                return 0 , 0
            
        if lenth == 2:
            rkd_type = data[0]['queueType']
            if rkd_type == "RANKED_SOLO_5x5":
                temp1 = data[0]
            else:
                temp1 = 0

            rkd_type = data[1]['queueType']
            if rkd_type == "RANKED_FLEX_SR":
                temp2 = data[1]
            else:
                temp2 = 0

            return temp1, temp2

    def put_rkd(self,pos,data):
        f = ttk.Frame(self.f_mat)
        f.place(relx=pos + 0.05, rely=0, relheight=1, relwidth= 0.25)
        f2 = ttk.Frame(self.f_mat)
        f2.place(relx=pos + 0.2, rely=0, relheight=1, relwidth= 0.25)

        if pos == 0:
            rkd_type = "Ranked Solo"
        else:
            rkd_type = "Ranked Flex"

        if data == 0:
            l1= ttk.Label(f2, text= rkd_type, anchor="center", justify=tk.CENTER)
            l1.pack(pady=0.01*self.window_y, fill = tk.X)
            l2= ttk.Label(f2, text= "Unranked", anchor="center", justify=tk.CENTER)
            l2.pack(pady=0.01*self.window_y, fill = tk.X)
            return


        if pos == 0:
            icon_num  = "Rank=" + data['tier'].capitalize() + ".png"
            cur_path = os.getcwd()
            icon_path = os.path.join(cur_path, 'assets', 'ranked-emblems-latest', 'Ranked Emblems Latest',icon_num)
            self.solo_img = Image.open(icon_path)
            len = round(0.17*self.window_y)
            self.solo_small = self.solo_img.resize((len,len), Image.Resampling.LANCZOS)
            self.solo_tk = ImageTk.PhotoImage(self.solo_small)
            l_icon = tk.Label(f, image = self.solo_tk)
            l_icon.place(relx=0, rely=0)
        else:
            icon_num  = "Rank=" + data['tier'].capitalize() + ".png"
            cur_path = os.getcwd()
            icon_path = os.path.join(cur_path, 'assets', 'ranked-emblems-latest', 'Ranked Emblems Latest',icon_num)
            self.flex_img = Image.open(icon_path)
            len = round(0.17*self.window_y)
            self.flex_small = self.flex_img.resize((len,len), Image.Resampling.LANCZOS)
            self.flex_tk = ImageTk.PhotoImage(self.flex_small)
            l_icon = tk.Label(f, image = self.flex_tk)
            l_icon.place(relx=0, rely=0)

        
        l1= ttk.Label(f2, text= rkd_type, anchor="center", justify=tk.CENTER)
        l1.pack(pady=0.01*self.window_y, fill = tk.X)
        l2= ttk.Label(f2, text= data['tier'].capitalize()+ " " + data['rank'] + " " + str(data['leaguePoints']) + " LP", anchor="center", justify=tk.CENTER)
        l2.pack(pady=0.01*self.window_y, fill = tk.X)
        wr = round(data['wins']/(data['wins'] + data['losses']),4)
        l3= ttk.Label(f2, text= str(data['wins']) + " wins " + str(data['losses']) + " losses", anchor="center", justify=tk.CENTER)
        l3.pack(pady=0.01*self.window_y, fill = tk.X)
        l4= ttk.Label(f2, text= "Win rate: " + str(wr*100) + "%", anchor="center", justify=tk.CENTER)
        l4.pack(pady=0.01*self.window_y, fill = tk.X)

    def question(self):
        messagebox.showerror("Info", "1. Only matches played in this patch is shown\n2. Replay works only if the replay file for that match is found in the folder")

    def tabs(self):
        f_tabs = ttk.Frame(master = self, border=10, relief=SUNKEN, width= 500, height= 200)
        f_tabs.place(relx=0, rely = 0.2, relheight=0.8, relwidth=0.1)
        l2 = ttk.Label(master = f_tabs, text="Tabs", bootstyle= "danger")
        l2.pack(anchor=CENTER)   

    def stats(self, mode):
        if mode == 0:
            self.f_stats = ttk.Frame(master = self, bootstyle = "info", border=10, relief=SUNKEN, width= 500, height= 200)
            self.f_stats.place(relx=0.1, rely = 0.2, relheight=0.8, relwidth=0.2)
        
        

        l1 = tk.Label(self.f_stats, text = "Raked Solo", anchor="center", justify=tk.CENTER)
        l1.pack(pady=0.01*self.window_y, fill = tk.X)

              

    def matches(self,mode):
        #mode 0 = init, 1 = update
        if mode == 0:
            self.f_mat = ttk.Frame(master = self, border=10, relief=SUNKEN, width= 500, height= 200)
            self.f_mat.place(relx=0.3, rely = 0, relheight=1, relwidth=0.7)
        else:
            for widget in self.f_mat.winfo_children():
                widget.destroy()

        with open("data.json","r") as file:
            data = json.load(file)
            region1 = data['region']
            region2 = data['region2']
            sumid = data['sumid']
            puuid = data['puuid']
            patch_start = data['patch_start']
            patch = data['patch']
            dir = data['dir']

        url2 = "https://"+ region2 +".api.riotgames.com/lol/league/v4/entries/by-summoner/" + sumid
        header = {"X-Riot-Token": self.api_key}
        resp2= requests.get(url2, headers = header)
        stat = resp2.status_code
        if self.handle_error(stat, "rkd") == 0:
            return
        rkd_data = resp2.json()
        solo_Q, flex_Q = self.process_rkd(rkd_data)
        if puuid == "K3NncqXpoXuEBjkd6wiNAmX4GxrPniIdIc5GMEnBiR9tQy3W5AQyh6bpZxoxtbooK9qat23qujeqBg":
            solo_Q['tier'] = "Challenger"
            solo_Q['rank'] = ""
        self.put_rkd(0,solo_Q)
        self.put_rkd(0.4,flex_Q)
        
        f_buttons = ttk.Frame(self.f_mat)
        f_buttons.place(relx= 0.8, rely=0, relheight=1, relwidth= 0.2)
        B_info = ttk.Button(f_buttons, text="?", command=self.question)
        B_info.pack(pady=0.01*self.window_y, fill = tk.X)
        rkd_ops = ["All", "Ranked Solo", "Ranked Flex", "5v5 Draft Pick", "5v5 Blind Pick","Custom"]
        om_rkd = tk.OptionMenu(f_buttons, self.rkd_type_selected, *rkd_ops, command= lambda rkd: self.list_match(rkd, puuid, region1, patch_start, patch))
        om_rkd.pack(pady=0.01*self.window_y, fill = tk.X)
        self.f_match_hist = ttk.Frame(master=self.f_mat)
        self.f_match_hist.place(relx=0, rely=0.2, relheight=0.8, relwidth=1)

        self.load_match(self.rkd_type_selected.get(),puuid,region1,patch_start, patch)

        f_pages = ttk.Frame(self.f_mat, border=1, relief=SUNKEN)
        f_pages.place(relheight=0.07,relwidth=1,relx=0, rely=0.93)
        self.turn_page(self.cur_page, region1, puuid, patch, dir)
        b_first = ttk.Button(f_pages, text = "<<", command=lambda: self.turn_page(0, region1, puuid, patch, dir))
        b_first.place(relx=0.3, rely=0.3)
        b_pre = ttk.Button(f_pages, text = "<", command=lambda: self.turn_page(self.cur_page-1, region1, puuid, patch, dir))
        b_pre.place(relx=0.5, rely=0.3)   
        b_next = ttk.Button(f_pages, text = ">", command=lambda: self.turn_page(self.cur_page+1, region1, puuid, patch, dir))
        b_next.place(relx=0.7, rely=0.3)

         

    

    def turn_page(self, page, region1, puuid, patch, dir):
        for widget in self.f_match_hist.winfo_children():
                widget.destroy()
        rag = 6
        self.cur_page = page
        if page < 0:
            page = 0
            self.cur_page = page
        if page >= self.max_page:
            page = self.max_page
            self.cur_page = page
            rag = self.match_hist_len - 6*self.max_page
        for i in range(rag):
            cur_index = page * 6 + i
            self.build_a_match(self.match_list[cur_index], region1, puuid, patch, i, dir)




    def load_match(self,rkd,puuid,region1,patch_start, patch):
        match rkd:
            case "All":
                Qid = ""
            case "Ranked Solo":
                Qid = "queue=420"
            case "Ranked Flex":
                Qid = "queue=440"
            case "5v5 Draft Pick":
                Qid = "queue=400"
            case "Custom":
                Qid = "queue=0"
            case "5v5 Blind Pick":
                Qid = "queue=430"

        url3 = "https://" + region1 + ".api.riotgames.com/lol/match/v5/matches/by-puuid/" + puuid + "/ids?startTime=" + str(patch_start) + "&" + Qid + "&count=100"
        header = {"X-Riot-Token": self.api_key}
        resp2= requests.get(url3, headers = header)
        stat = resp2.status_code
        if self.handle_error(stat, "match list") == 0:
            return
        self.match_list = resp2.json()
        self.match_hist_len = len(self.match_list)
        self.max_page = math.ceil(self.match_hist_len/6)



    def build_a_match(self, game, region1, puuid, patch, pos, dir):
        f = ttk.Frame(self.f_match_hist, border=1, relief=SUNKEN)
        f.place(relheight=0.15,relwidth=1,relx=0, rely=0.15*pos)
        url = "https://" + region1 + ".api.riotgames.com/lol/match/v5/matches/" + game
        header = {"X-Riot-Token": self.api_key}
        resp= requests.get(url, headers = header)
        stat = resp.status_code
        if self.handle_error(stat, "build each match") == 0:
            return
        match = resp.json()
        with open("match_data.json","w") as file:
                json.dump(match, file, indent=4)
        ids = match["metadata"]["participants"]
        user_pos = ids.index(puuid)
        user_info = match["info"]["participants"][user_pos]
        queue = match["info"]["queueId"]
        finish = match["info"]["gameEndTimestamp"]
        duration = match["info"]["gameDuration"]
        user_champ = user_info["championName"]
        user_Champ_id = user_info["championId"]
        kills = user_info["kills"]
        death = user_info["deaths"]
        asist = user_info["assists"]
        neu_cs = user_info["neutralMinionsKilled"]
        minion_cs = user_info["totalMinionsKilled"]
        dmg = user_info["totalDamageDealtToChampions"]
        gold = user_info["goldEarned"]

        if user_pos > 4:
            range_value = (5,10)
            opnent = user_pos - 5
        else:
            range_value = (0,5)
            opnent = user_pos + 5
        

        match queue:
            case 420:
                Qid = "Ranked Solo"
            case 440:
                Qid = "Ranked Flex"
            case 400:
                Qid = "5v5 Draft"
            case 0:
                Qid = "Custom"
            case 430:
                Qid = "5v5 Blind"
        l1= tk.Label(f, text=Qid)
        l1.place(relx=0.018,rely=0.1)
        
        
        if user_info["win"] == 1:
            result = "Victory"
            l2 = ttk.Label(f, text=result,bootstyle="inverse-success")
            #f.config(bootstyle="success")
        else:
            result = "Defeat"
            l2 = ttk.Label(f, text=result,bootstyle="inverse-danger")
            #f.config(bootstyle="danger")  
        l2.place(relx=0.02,rely=0.4)

        current_time = int(time.time())
        time_difference = current_time - round(finish/1000)
        days, remainder = divmod(time_difference, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days == 0:
            if hours == 0:
                ago = str(minutes) + " mins ago"
            else:
                ago = str(hours) + " hours ago"
        else:
            ago = str(days) + " days ago"
        l3 = ttk.Label(f, text=ago)
        l3.place(relx=0.018,rely=0.7)
        
        cur_path = os.getcwd()
        champ_path = os.path.join(cur_path, 'assets', 'dragontail-' + str(patch), patch, 'img', 'champion', user_champ + ".png")
        champ_img = Image.open(champ_path)
        len = round(0.1*self.window_y)
        champ_small = champ_img.resize((len,len), Image.Resampling.LANCZOS)
        self.champ_tks[pos] = ImageTk.PhotoImage(champ_small)
        l4 = tk.Label(f, image = self.champ_tks[pos])
        l4.place(relx=0.1,rely=0.05)


        l5 = tk.Label(f, text=str(kills) + "/" + str(death) + "/" + str(asist))
        l5.place(relx=0.2,rely=0.2)

        if death == 0:
            temp_death = 1
        else: 
            temp_death = death
        kda = round((kills + asist)/temp_death,2)
        l6 = tk.Label(f, text=str(kda) + ":1 KDA")
        l6.place(relx=0.2, rely=0.5)

        sp = ttk.Separator(f, orient='vertical')
        sp.place(relx = 0.3, rely=0.1, relheight=0.8)

        hours2, remainder = divmod(duration, 3600)
        minutes2, seconds2 = divmod(remainder, 60)
        if hours2 == 0:
            dur = "Duration: " + str(minutes2) + "mins " + str(seconds2) + "s"
        else:
            dur = "Duration: " + str(hours2) + "hours " + str(minutes2) + "mins"
        l7 = tk.Label(f, text= dur)
        l7.place(relx = 0.35, rely=0.1)

        l8 = tk.Label(f, text="CS: " + str(neu_cs + minion_cs))
        l8.place(relx = 0.35, rely=0.25)

        team_kill = 0
        for i in range(*range_value):
            team_kill = team_kill + match["info"]["participants"][i]["kills"]
        if team_kill == 0:
            KP = 0
        else:
            KP = round((kills + asist)/team_kill,2)*100
        l9 = tk.Label(f, text="KP: " + str(int(KP)) + "%")
        l9.place(relx = 0.35, rely=0.4)

        team_dmg = 0
        for i in range(*range_value):
            team_dmg = team_dmg + match["info"]["participants"][i]["totalDamageDealtToChampions"]
        if team_dmg == 0:
            dmg_perct = 0
        else:
            dmg_perct = round(dmg/team_dmg,2)*100
        l10 = tk.Label(f, text="Damage Share: " + str(int(dmg_perct)) + "%")
        l10.place(relx = 0.35, rely=0.55)

        opn_gold = match["info"]["participants"][opnent]["goldEarned"]
        golf_diff = gold - opn_gold
        l11 = tk.Label(f, text= "Lane Gold Diff: " + str(golf_diff))
        l11.place(relx = 0.35, rely=0.7)

        sp2 = ttk.Separator(f, orient='vertical')
        sp2.place(relx = 0.5, rely=0.1, relheight=0.8)

        for i in range(10):
            if i > 4:
                padx = 0.2
                pady = i - 5
            else:
                padx = 0
                pady = i
            cur_champ = match["info"]["participants"][i]["championName"]
            cur_name = match["info"]["participants"][i]["riotIdGameName"]
            cur_tag = match["info"]["participants"][i]["riotIdTagline"]
            champ_path = os.path.join(cur_path, 'assets', 'dragontail-' + str(patch), patch, 'img', 'champion', cur_champ + ".png")
            champ_img = Image.open(champ_path)
            len = round(0.021*self.window_y)
            champ_small = champ_img.resize((len,len), Image.Resampling.LANCZOS)
            self.champ_icons[(pos-1)*10+i] = ImageTk.PhotoImage(champ_small)
            l = tk.Label(f, image = self.champ_icons[(pos-1)*10+i])
            l.place(relx=0.52 + padx, rely=0.02 + 0.18*pady)

            self.style.configure('Link.TButton', font=('Helvetica', 8))
            #self.player_buttons[i] = ttk.Button(f, text=cur_name, style='Link.TButton', command=self.load_player)
            #self.player_buttons[i].place(relx=0.54,rely=0 + 0.18*i)
            l2 = tk.Label(f, text=cur_name, cursor="hand2")
            l2.place(relx=0.54 + padx, rely=0.02 + 0.18*pady)
            l2.bind("<Button-1>", lambda e, name=cur_name: self.load_player(name))

        game = game.replace('_', '-')
        replay_file = game + ".rofl"
        path = dir + "/" + replay_file
        if os.path.isfile(path):
            b12 = ttk.Button(f, text="Analyse Replay", style=SUCCESS, command=lambda: self.analyse_replay(path))
            b12.place(relx = 0.9, rely=0.4)
        else:
            b12 = ttk.Button(f, text="Replay not found", style=DANGER, command=lambda: self.analyse_replay(path))
            b12.place(relx = 0.9, rely=0.4)



        


    
    def analyse_replay(self,path):
        print("Analysing" + path)        

    def load_player(self, name):
        print(name)
        pass




            
        

   

   




#root = tk.Tk()
#root.title("Replay Academy")
#menu_main = Menu_Main(master=root)
#root.geometry(str(menu_main.Frame_X) + "x" + str(menu_main.Frame_y))



#root.mainloop()
