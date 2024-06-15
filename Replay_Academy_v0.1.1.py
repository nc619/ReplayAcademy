#Replay Academy v0.1.1
#Initial trial to get data from API

import requests
import json
import numpy as np
import time
import urllib.request, json 
from numba import njit
from datetime import date, timedelta, datetime
today = datetime.today()

def argmin(my_list, substract):
    min = 5000
    for i, k in enumerate(my_list):
        value = abs(k-substract).days
        if i==0 or value < min:
            min = i
    return min

def findLastPatch():
    patches = [date(2023, 12, 6), date(2024, 1, 10)]
    today = date.today()
    for i in range(2,25):
        if i == 13 or i == 24:
            patches.append(patches[i-1]+timedelta(days=21))    
        else:
            patches.append(patches[i-1]+timedelta(days=14))    
    last_patch = patches[argmin(patches,today)]
    return last_patch

print("\nReplay academy\n")

name = "Penetrasion#EUW"
apikey_raw = "RGAPI-08a8b9ca-3f11-4f00-afd6-7daf49542a50"
#startTime= "1672531200"
lp = findLastPatch()
lp_time = datetime.timestamp(datetime.combine(lp,datetime.min.time()))
startTime = str(int(lp_time))
curTime=str(int(time.time()))
versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
with urllib.request.urlopen(versions_url) as url:
    versions = json.load(url)
    version = versions[0]
champion_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"

class UserInfo:
    def __init__(self, name, api) -> None:
        self.apikey = api
        self.name = name
        self.id, self.accID, self.puuid, self.icon, self.revision_date, self.level = self.getInfoFromName()
        #what they are: 
        
    def getInfoFromName(self): 
        """
        Args: Class UserInfo 
        Returns: User id,accID,puuid,icon,revision_data,level. Details at: https://developer.riotgames.com/apis#summoner-v4/GET_getBySummonerName
        Note: Now it use Name ONLY to find all other info, later it can be anthing
        
        """
        resp= requests.get("https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + self.name + "?api_key=" + self.apikey)
        resp_json=resp.json()
        id=resp_json["id"]
        accID=resp_json["accountId"]
        puuid=resp_json["puuid"]
        icon=resp_json["profileIconId"]
        revision_data=resp_json["revisionDate"]
        level=resp_json["summonerLevel"]
        return id,accID,puuid,icon,revision_data,level
    
    def getMatchList(self,startTime,curTime,count): #To do Alvin: count & Q type & start
        """
        Args: Class UserInfo, startTime = earliest date (epoch in sec), curTime= current time (epoch in sec), count = number of matches to find
        Returns: A list of match IDs given by riot API
        Note: It uses UserInfo.puuid
        """
        resp= requests.get("https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/" + self.puuid +"/ids?startTime=" + startTime + "&endTime=" + curTime +"&count=" + str(count) + "&api_key=" + self.apikey)
        matches= resp.json()
        return matches
    
"""     def getMatchDetails(self,game_num):#To do Alvin: put count and pop error if num is outside count
      
        (Args: Class UserInfo, game_num = index of the game in UserInfo.match_list (counting from back)
        Returns: Match details in json
        Note: It used UserInfo.match_list)
   
        matchID=self.match_list[-game_num]
        resp = requests.get("https://europe.api.riotgames.com/lol/match/v5/matches/" + matchID + "?api_key=" +self.apikey)
        match_details=resp.json()
        return match_details
    
    def getMatchTimeline(self,game_num):

        (Args: Class UserInfo, game_num = index of the game in UserInfo.match_list (counting from back)
        Returns: Match timeline in json
        Note: It used UserInfo.match_list)

        matchID=self.match_list[-game_num]
        resp = requests.get("https://europe.api.riotgames.com/lol/match/v5/matches/" + matchID + "/timeline?api_key=" + self.apikey)
        match_timeline = resp.json()
        return match_timeline """


class Match:
    def __init__(self,matchID,api) -> None:
        self.matchID = matchID
        self.apikey = api
        self.matchDetails = self.getMatchDetails()
        self.matchTimeline = self.getMatchTimeline()

    def getMatchDetails(self):#To do Alvin: put count and pop error if num is outside count
        """
        Args: Class UserInfo, game_num = index of the game in UserInfo.match_list (counting from back)
        Returns: Match details in json
        Note: It used UserInfo.match_list
        """
        resp = requests.get("https://europe.api.riotgames.com/lol/match/v5/matches/" + self.matchID + "?api_key=" +self.apikey)
        match_details=resp.json()
        return match_details
    
    def getMatchTimeline(self):
        """
        Args: Class UserInfo, game_num = index of the game in UserInfo.match_list (counting from back)
        Returns: Match timeline in json
        Note: It used UserInfo.match_list
        """
        resp = requests.get("https://europe.api.riotgames.com/lol/match/v5/matches/" + self.matchID + "/timeline?api_key=" + self.apikey)
        match_timeline = resp.json()
        return match_timeline

    
class SpiderMatches:
    def __init__(self,api, champ_dict) -> None:
        """Initialise the class

        Args:
            api (string): API of ReplayAcademy 
            champ_dict (_type_): Dictionary containing all the champions
        """
        self.matchList = []
        N_champs = len(champ_dict)
        self.champ_dict = champ_dict
        self.champGrid = np.zeros((N_champs, N_champs,2))
        self.apikey = api
        self.unexplored_players = []
        self.explored_players = []
        self.unexplored_matches = []
        
    def getMatchList(self, puuid, count):
        resp = requests.get("https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/" + puuid +"/ids?startTime=" + startTime + "&endTime=" + curTime +"&count=" + str(count) + "&api_key=" + self.apikey)
        matches= resp.json()
        return matches
    
    def updateLists(self, matchID):
        curr_match = Match(matchID, self.apikey)
        participants = curr_match.getMatchDetails()['info']['participants']
        self.unexplored_players.append([i for i in participants if i not in self.explored_players])
        new_player =  participants[np.random.choice([i for i in range(10)])]['puuid']
        match_list = self.getMatchList(new_player, 20)
        
        for k in range(10): 
            if  k != 0 and k%10 == 0:
                new_player =  participants[np.random.choice([i for i in range(10)])]['puuid']
            new_player = participants[k]['puuid']
            match_list = self.getMatchList(new_player, 20)
            k=k+1
    
    def getNewMatch(self, matchID, count = 10):
        curr_match = Match(matchID, self.apikey)
        participants = curr_match.getMatchDetails()['info']['participants']
        new_player =  participants[np.random.choice([i for i in range(10)])]['puuid']
        match_list = self.getMatchList(new_player, count)
        k = 0
        while type(match_list) != list or k < 10: 
            if  k != 0 and k%10 == 0:
                new_player =  participants[np.random.choice([i for i in range(10)])]['puuid']
            new_player = participants[k]['puuid']
            match_list = self.getMatchList(new_player, count)
            k=k+1
        rand_match = match_list[np.random.choice([i for i in range(len(match_list))])]
        match_type = Match(rand_match,self.apikey).getMatchDetails()['info']['gameMode']
        if rand_match in self.matchList or match_type != 'CLASSIC':
            found_flag = False
            for i in range(len(match_list)):
                rand_match = match_list[i]
                match_type = Match(rand_match,self.apikey).getMatchDetails()['info']['gameMode']
                if rand_match not in self.matchList and match_type == 'CLASSIC':
                    found_flag = True
                    break
            if not found_flag:
                return self.getNewMatch(matchID, count = count+10)
        if match_type != 'CLASSIC': raise("WTF")
        return rand_match
    
    def getStats(self, matchID, N, gameMode = 'CLASSIC'):
        self.matchList.append(matchID)
        for i in range(N):
            self.updateGrid(matchID, N, gameMode = gameMode)
            matchID = self.getNewMatch(matchID)
            self.matchList.append(matchID)

    
    def checkPlayer(self, player_ID, N, match_args,gameMode = 'CLASSIC'):
        self.explored_players.append(player_ID)
        match_list = player_ID.getMatchList(match_args['Start'],match_args['Curr'],match_args['N_matches'])
        self.unexplored_matches.append([i for i in match_list if i not in self.matchList])
        for match_ID in match_list:
            if match_ID in self.matchList:
                continue
            self.unexplored_matches.append(match_ID)
            match = Match(match_ID,self.apikey)
            players = [match.getMatchDetails()['info']['participants'][k]['puuid'] for k in range(10)]
            for player in players:
                if player not in self.explored_players: self.unexplored_players.append(player)
    
    def exploreMatches(self, gameMode = 'CLASSIC'):
        if self.unexplored_matches == []:
            pass
        else:
            for match_ID in self.unexplored_matches:
                self.updateGrid(match_ID, gameMode=gameMode)
    
    def updateGrid(self, matchID, N, gameMode = 'CLASSIC'):
        if type(matchID) == str:
            #iterator_dict = {0: (0,5), 1: (5,10)}
            curr_match = Match(matchID,self.apikey).getMatchDetails()
            other_players = curr_match['info']['participants'][5:]
            for p_i, player in enumerate(curr_match['info']['participants'][0:5]):
                #other_players=curr_match['info']['participants'][iterator_dict[p_i//5][0]:iterator_dict[p_i//5][1]]
                p_ID = self.champ_dict[f"{player['championName'][0]}{player['championName'][1:].lower()}"]
                for op in other_players:
                    id_dict = {0: player, 1: op}
                    op_ID = self.champ_dict[f"{op['championName'][0]}{op['championName'][1:].lower()}"]
                    ids = [p_ID, op_ID]
                    ax = np.argsort(ids)
                    self.champGrid[ids[ax[0]],ids[ax[1]],0] += int(id_dict[ax[0]]['win'])
                    self.champGrid[ids[ax[0]],ids[ax[1]],1] += 1
    
    def getStats2(self, matchID, N, match_args, initial_players,gamemode = 'CLASSIC'):
        pass
            


#if Nico == gay:
EUW1Lee = UserInfo(name,apikey_raw)
EUW1Lee.match_list=EUW1Lee.getMatchList(startTime,curTime,20)
curMatch = Match(EUW1Lee.match_list[-1],apikey_raw)
with urllib.request.urlopen(champion_url) as url:
    champ_json = json.load(url)

champ_dict = {}
for i,champ_name in enumerate(champ_json['data']):
    champ_dict[f"{champ_name[0]}{champ_name[1:].lower()}"] = i

sm = SpiderMatches(apikey_raw, champ_dict)
sm.getStats(EUW1Lee.match_list[-1],10000)
#sm.getMatches(EUW1Lee.match_list[-1],10)



print("\nUR blessed\n")