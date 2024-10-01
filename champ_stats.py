import os
import requests
import json
import random
import time

class Champ_stats():

    api_key = "RGAPI-606ef5aa-a9be-4c2c-9e92-fcf858b97492"
    seed_puuid = "qLKSqqbb8dusevo8BNdW5CCy1Y0EsGwUtvjoZMDi0QBjfBz5dDgr58HN2qHpxeSaBM1g18NEEQeOIg"
    data = {0:{},1:{},2:{},3:{},4:{}}
    data_min = {0:{'gold':[],'xp':[],'total_gold':[]},1:{'gold':[],'xp':[],'total_gold':[]},2:{'gold':[],'xp':[],'total_gold':[]},3:{'gold':[],'xp':[],'total_gold':[]},4:{'gold':[],'xp':[],'total_gold':[]}}
    server = "europe"
    server2 = "EUW1"


    def __init__(self):
        self.cur_player = self.seed_puuid
        self.matches = self.get_match_list(self.seed_puuid)


        
        
    def get_match_list(self, puuid):
        url = "https://" + self.server + ".api.riotgames.com/lol/match/v5/matches/by-puuid/" + puuid + "/ids?queue=420&start=0&count=20"
        header = {"X-Riot-Token": self.api_key}
        resp= requests.get(url, headers = header)
        stat = resp.status_code
        if stat == 200:
            resp = resp.json()
            return resp
        else:
            print("Error getting matche list, error", stat)

    def get_champ_data(self, data, pos):
        #0 = top, 1 = jgl, 2mid,  3adc, 4sup
        resp = data
        info1 = resp["info"]["participants"][pos]
        info2 = resp["info"]["participants"][pos+5] 
        matchid = resp["metadata"]["matchId"]
        return info1,info2, matchid

    def get_players(self, match_id, pos):
        url = "https://" + self.server + ".api.riotgames.com/lol/match/v5/matches/" + match_id
        header = {"X-Riot-Token": self.api_key}
        resp= requests.get(url, headers = header)
        stat = resp.status_code
        if stat == 200:
            resp = resp.json()
            player = resp["metadata"]["participants"][pos]
            sumid = resp["info"]["participants"][pos]["summonerId"]
            return player, sumid, resp
        else:
            print("Error getting reading a match2, error", stat)

    def get_elo(self, elo, sumid):
        if elo == 0:
            return 1
        url2 = "https://"+ self.server2 +".api.riotgames.com/lol/league/v4/entries/by-summoner/" + sumid
        header = {"X-Riot-Token": self.api_key}
        resp= requests.get(url2, headers = header)
        stat = resp.status_code
        if stat == 200:
            resp = resp.json()
            if len(resp) > 0 and elo == resp[0].get('tier',0):
                return 1
            else:
                return 0
        else:
            print("Error getting get_elo, error", stat)




    def get_next_player(self,cur_player, elo, last_match):
        #elo = 0, all elo
        flag = 1
        matches = self.matches
        match_n = 1
        tried_numbers = set()
        data = {}
        while flag == 1:
            if len(tried_numbers) >= 10:
                match_n = match_n + 1
                tried_numbers = set()
            if matches[match_n] == last_match:
                match_n += 1
            if match_n >= len(self.matches):
                return self.seed_puuid
            
            rand = random.randint(0, 9)
            if rand in tried_numbers:
                continue
            tried_numbers.add(rand)
            next_player, sumid, data= self.get_players(matches[match_n], rand)
            same_elo = self.get_elo(elo, sumid)
            if same_elo == 0:
                continue
            matches_next = self.get_match_list(next_player)
            if len(matches_next) >= 3:
                flag = 0
            if next_player == cur_player:
                flag = 1
        self.matches = matches_next
        return next_player, data, matches[match_n]
    
    def update_data(self, champ_data, pos):
        champ = champ_data["championName"]
        if champ not in self.data[pos]:
            self.data[pos][champ] = {'kills': [], 'deaths': [], 'assists': [], 'games': 0, 'wins': 0, 'totaldmg': [], 'totaldmgtaken': [], 'turrentTakedowns': [], 'totalgold':[], 'earlylead':[], 'initialbuff':[], 'jglcs10min':[],'laningphaselead':[], 'takedownsFirstXMinutes':[], 'voidMonsterKill':[], 'teamRiftHeraldKills':[]}
    
        # Update the stats for the champion
        self.data[pos][champ]['kills'].append(champ_data["kills"])
        self.data[pos][champ]['deaths'].append(champ_data["deaths"])
        self.data[pos][champ]['assists'].append(champ_data["assists"])
        self.data[pos][champ]['games'] += 1
        self.data[pos][champ]['totaldmg'].append(champ_data["totalDamageDealtToChampions"])
        self.data[pos][champ]['totaldmgtaken'].append(champ_data["totalDamageTaken"])
        self.data[pos][champ]['turrentTakedowns'].append(champ_data["turretTakedowns"])
        self.data[pos][champ]['totalgold'].append(champ_data["goldEarned"])
        self.data[pos][champ]['earlylead'].append(champ_data["challenges"].get("earlyLaningPhaseGoldExpAdvantage",0))
        self.data[pos][champ]['initialbuff'].append(champ_data["challenges"].get("initialBuffCount",0))
        self.data[pos][champ]['jglcs10min'].append(champ_data["challenges"].get("jungleCsBefore10Minutes",0))
        self.data[pos][champ]['laningphaselead'].append(champ_data["challenges"].get("laningPhaseGoldExpAdvantage",0))
        self.data[pos][champ]['takedownsFirstXMinutes'].append(champ_data["challenges"].get("takedownsFirstXMinutes",0))
        self.data[pos][champ]['voidMonsterKill'].append(champ_data["challenges"].get("voidMonsterKill",0))
        self.data[pos][champ]['teamRiftHeraldKills'].append(champ_data["challenges"].get("teamRiftHeraldKills",0))
        if champ_data["win"] == True:
            self.data[pos][champ]['wins'] += 1





    def cs_main_loop(self, seed_player, roles, elo):
        #roles = 1 to 5
        last_player = seed_player
        last_game = ""
        for pos in range(roles):
            for iter in range(60):
                cur_player, cur_game_data, cur_game = self.get_next_player(last_player,elo, last_game)
                print(last_game + "     " + cur_game )
                if last_game == cur_game:
                    print("same game")
                    cur_game = self.matches[1] 


                champ_data_temp, champ_data_temp2, matchid= self.get_champ_data(cur_game_data, pos)
                champ = champ_data_temp["championName"]
                name = champ_data_temp["riotIdGameName"]
                tag = champ_data_temp["riotIdTagline"]
                print("Elo: "+ elo + "  Role:" + str(pos) + "   iter:" + str(iter) + "   champ:" + champ + "      " +name + "        " + tag +"      " + matchid + cur_game)
                self.update_data( champ_data_temp, pos)

                champ = champ_data_temp2["championName"]
                name = champ_data_temp2["riotIdGameName"]
                tag = champ_data_temp2["riotIdTagline"]
                print("Elo: "+ elo + "  Role:" + str(pos) + "   iter:" + str(iter) + "   champ:" + champ + "      " +name + "        " + tag +"      " + matchid + cur_game)
                self.update_data( champ_data_temp2, pos)

                last_game = cur_game
                last_player = cur_player
                time.sleep(2.6)

                file_name = elo + "_champ_stats.json"
                with open(file_name,"w") as file:
                    json.dump(self.data, file, indent=4)

        file_name = elo + "_champ_stats.json"
        with open(file_name,"w") as file:
            json.dump(self.data, file, indent=4)





    def cs_loop_mins(self,seed_player, roles, elo):
        #roles = 1 to 5
        last_player = seed_player
        last_game = ""
        for pos in range(roles):
            for iter in range(20):
                cur_player, cur_game_data, cur_game = self.get_next_player(last_player,elo, last_game)
                print(last_game + "     " + cur_game )
                if last_game == cur_game:
                    print("same game")
                    cur_game = self.matches[1] 


                list_gold, list_xp, list_gold2, list_xp2, ttgold, ttgold2 = self.get_mins(cur_game, pos)
                self.data_min[pos]['gold'].append(list_gold)
                self.data_min[pos]['xp'].append(list_xp)
                self.data_min[pos]['total_gold'].append(ttgold)
                self.data_min[pos]['gold'].append(list_gold2)
                self.data_min[pos]['xp'].append(list_xp2)
                self.data_min[pos]['total_gold'].append(ttgold2)
                print(list_gold, list_xp)

                last_game = cur_game
                last_player = cur_player
                time.sleep(2.6)

                file_name = elo + "_champ_mins.json"
                with open(file_name,"w") as file:
                    json.dump(self.data_min, file, indent=4)

        file_name = elo + "_champ_mins.json"
        with open(file_name,"w") as file:
            json.dump(self.data_min, file, indent=4)


    def get_mins(self, match_id, pos):
        list_gold = []
        list_xp = []
        list_total_gold = []
        list_gold2 = []
        list_xp2 = []
        list_total_gold2 = []
        gold_last = 0
        gold_last2 = 0
        url = "https://" + self.server + ".api.riotgames.com/lol/match/v5/matches/" + match_id +"/timeline"
        header = {"X-Riot-Token": self.api_key}
        resp= requests.get(url, headers = header)
        stat = resp.status_code
        if stat == 200:
            resp = resp.json()
            resp = resp["info"]["frames"]
            for frame in resp:
                gold_temp = frame["participantFrames"][str(pos+1)]["totalGold"]
                level = frame["participantFrames"][str(pos+1)]["level"]
                list_total_gold.append(gold_temp)
                list_gold.append(gold_temp - gold_last)
                gold_last = gold_temp
                list_xp.append(level)
                gold_temp2 = frame["participantFrames"][str(pos+6)]["totalGold"]
                level2 = frame["participantFrames"][str(pos+6)]["level"]
                list_total_gold2.append(gold_temp2)
                list_gold2.append(gold_temp2 - gold_last2)
                gold_last2 = gold_temp2
                list_xp2.append(level2)
            return list_gold, list_xp, list_gold2, list_xp2, list_total_gold, list_total_gold2
        else:
            print("Error getting reading a timeline, error", stat)

    



cs = Champ_stats()
#cs.cs_main_loop(cs.seed_puuid, 1, "EMERALD")
cs.cs_loop_mins(cs.seed_puuid, 1, "EMERALD")