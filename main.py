#RA

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import json
import requests

from Main_menu import Menu_Main

#for later: change config at first start, updata, store and structutr the data dragon
#for later: turn the page, make replay file finder and button to replay
#for later: player redirect button
#Remeber: the datadragon structure and update protocol, change the patch_start time


class RA():
    #store initial and global stuff
    flag_sign = 0
    cur_page =0 #0=none, 1=main menu
    flag_main_menu_ready = 0
    patch_start = 1715742000 #epoch time when 13.10 goes live (need to hard code since its not fixed or fetched)
    
    def __init__(self):
        self.check_data()
        self.check_patch()

    def check_patch(self):
        patch = self.ask_patch()
        with open("data.json","r") as file:
            data = json.load(file)
            if 'patch' in data:
                if patch == data['patch']:
                    return
                else:
                    self.update(patch)
            else:
                data['patch'] = patch
                data['patch_start'] = self.patch_start
                with open("data.json","w") as file:
                    json.dump(data, file)

    def ask_patch(self):
        url = "https://ddragon.leagueoflegends.com/api/versions.json"
        response = requests.get(url)
        if response.status_code == 200:
            versions = response.json()
            return versions[0]
        else:
            return None
    
    def update(self, patch):
        #to do: automate the update of data dragon
        with open("data.json","r") as file:
            data = json.load(file)
            data['patch_start'] = self.patch_start
            data['patch'] = patch
        with open("data.json","w") as file:
                    json.dump(data, file)
        print("Updated to" + str(patch))
        



    def check_data(self):
        self.Frame_X, self.Frame_y = self.get_reso()
        try:
            with open("data.json","r") as file:
                data = json.load(file)
                if 'flag_sign' in data:
                    self.flag_sign = data['flag_sign']
                else: 
                    return
        except FileNotFoundError:
            with open("data.json","w") as file:
                json.dump({}, file)
                self.flag_sign = 0
                return


            
    def switch_main_menu(self, root):
        if self.flag_main_menu_ready == 0:
            self.main_menu = Menu_Main(self.Frame_y, self.flag_sign, master = root)
            self.cur_page = 1
        else:
            #hide all and make menumain visible
            pass

    def get_reso(self):
        x=1600
        y=900
        return x,y

      
app = RA()
root = tk.Tk()
root.geometry(str(app.Frame_X) + "x" + str(app.Frame_y))
root.title("Replay Academy")
app.switch_main_menu(root)




root.mainloop()
