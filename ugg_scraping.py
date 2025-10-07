# from urllib.request import urlopen
# url = "https://u.gg/lol/champions/riven/counter"
# page = urlopen(url)
# print(page)
# html_bytes = page.read()
# html = html_bytes.decode("utf-8")
# print(html)

# import requests

# headers = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
# }

import numpy as np

class statsData:
    def __init__(self, champ_dict) -> None:
        self.n_champs = len(champ_dict)
        self.champ_dict = champ_dict
        # Initialize square matrix with zeros
        self.data = np.zeros((self.n_champs, self.n_champs))
    
    def update_matchup(self, champ1, champ2, value):
        """Update matchup data between two champions"""
        if champ1 == "alistar":
            pass
        if "nunu" in champ2.lower() or "renata" in champ2.lower():
            champ2 = champ2.split(" ")[0]
        champ1 = champ1.replace("'","").replace(" ","").replace("-","").replace(".","").lower()
        champ2 = champ2.replace("'","").replace(" ","").replace("-","").replace(".","").lower()
        if champ1 in self.champ_dict and champ2 in self.champ_dict:
            i = self.champ_dict[champ1]
            j = self.champ_dict[champ2]
            self.data[i][j] = value
        else:
            raise("Champion name was incorrect \nNote: for Nunu & Willump, champ name is just Nunu and for Renata Glasc champ name is just Renata.")
    
    def get_matchup(self, champ1, champ2):
        """Get matchup data between two champions"""
        if "nunu" in champ2 or "renata" in champ2:
            champ2 = champ2.split(" ")[0]
        champ1 = champ1.replace("'","").replace(" ","").replace("-","").replace(".","").lower()
        champ2 = champ2.replace("'","").replace(" ","").replace("-","").replace(".","").lower()
        if champ1 in self.champ_dict and champ2 in self.champ_dict:
            i = self.champ_dict[champ1]
            j = self.champ_dict[champ2]
            return self.data[i][j]
        return None

class gameStats:
    def __init__(self, champ_dict, mode = "create") -> None:
        self.roles = ['top', 'jungle', 'mid', 'adc', 'support']
        self.champ_dict = champ_dict
        self.processed_champions = set()
        
        # Create nested dictionaries for each stat type and role
        self.winrate = {role: statsData(champ_dict) for role in self.roles}
        self.ngames = {role: statsData(champ_dict) for role in self.roles}
        self.gold_diff = {role: statsData(champ_dict) for role in self.roles}
        
        if mode == "load":
            self._load_data()
        else:
            self._populate_all_data()
    
    def _populate_all_data(self):
        """Populates data for all champions in all roles"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        try:
            for champion in self.champ_dict.keys():
                if champion not in self.processed_champions:
                    print(f"Processing {champion}...")
                    for role in self.roles:
                        print(f"  Role: {role}")
                        self._populate_data(champion, role, driver)
                    self.processed_champions.add(champion)
                    self._save_progress()
        finally:
            driver.quit()
        
    
    def _save_progress(self):
        """Save current progress to files"""
        try:
            for role in self.roles:
                np.save(f'winrate_data_{role}.npy', self.winrate[role].data)
                np.save(f'ngames_data_{role}.npy', self.ngames[role].data)
                np.save(f'gold_diff_data_{role}.npy', self.gold_diff[role].data)
            
            with open('processed_champions.json', 'w') as f:
                json.dump(list(self.processed_champions), f)
        except Exception as e:
            print(f"Error saving progress: {str(e)}")
    
    def _load_data(self):
        """Load previously saved data"""
        try:
            for role in self.roles:
                self.winrate[role].data = np.load(f'winrate_data_{role}.npy')
                self.ngames[role].data = np.load(f'ngames_data_{role}.npy')
                self.gold_diff[role].data = np.load(f'gold_diff_data_{role}.npy')
            
            with open('processed_champions.json', 'r') as f:
                self.processed_champions = set(json.load(f))
        except Exception as e:
            print(f"Error loading data: {str(e)}")
    
    def get_winrate(self, champ1, champ2, role):
        """Get winrate for champ1 vs champ2 matchup in specific role"""
        return self.winrate[role].get_matchup(champ1, champ2)
    
    def get_ngames(self, champ1, champ2, role):
        """Get number of games played for champ1 vs champ2 matchup in specific role"""
        return self.ngames[role].get_matchup(champ1, champ2)
    
    def get_golddiff(self, champ1, champ2, role):
        """Get average gold difference for champ1 vs champ2 matchup in specific role"""
        return self.gold_diff[role].get_matchup(champ1, champ2)

    def _find_list_container_by_header(self, driver, header_prefix):
        header = WebDriverWait(driver, 15).until(EC.presence_of_element_located((
            By.XPATH,
            f"//div[@id='content']//div[starts-with(normalize-space(), '{header_prefix}') ]"
        )))
        return header.find_element(By.XPATH, "following-sibling::div[contains(@class,'overflow-auto')][1]")

    def _extract_rows(self, list_container):
        return list_container.find_elements(By.XPATH, ".//a[contains(@class,'items-center')]")

    def _parse_common_row(self, row):
        name = row.find_element(By.XPATH, "./div[2]//div[contains(@class,'font-bold')]").text
        games_text = row.find_element(By.XPATH, "./div[3]//div[contains(., 'games')]").text
        games = int(games_text.split(' ')[0].replace(',', ''))
        return name, games

    def _parse_wr_row(self, row):
        wr_text = row.find_element(By.XPATH, "./div[3]//div[contains(@class,'font-bold')]").text
        wr = float(wr_text.split('%')[0])
        name, games = self._parse_common_row(row)
        return name, wr, games

    def _parse_gd15_row(self, row):
        gd_text = row.find_element(By.XPATH, "./div[3]//div[contains(@class,'font-bold')]").text
        first_token = gd_text.split(' ')[0].replace('+','')
        gd_val = float(first_token)
        name, games = self._parse_common_row(row)
        return name, gd_val, games

    def _populate_data(self, champion, role, driver):
        """Scrapes and populates matchup data for a given champion in a specific role"""
        url = f"https://u.gg/lol/champions/{champion}/counter?role={role}"
        driver.get(url)

        try:
            # Handle consent button
            consent_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'fc-cta-consent')]"))
            )
            consent_button.click()
        except:
            pass

        # try:
        #     # Click "See More Champions" (legacy; may not exist anymore)
        #     see_more_button = WebDriverWait(driver, 5).until(
        #         EC.element_to_be_clickable((By.XPATH, "//div[text()='See More Champions']"))
        #     )
        #     see_more_button.click()
        # except:
        #     pass

        try:
            # Locate third column (GD15) by its header, then parse rows
            gd_list = None
            try:
                gd_list = self._find_list_container_by_header(driver, "Best Lane Counters vs")
            except Exception:
                gd_list = None

            # Locate WR column by header (try Worst Picks vs, then Best Picks vs)
            wr_list = None
            for header_prefix in ["Worst Picks vs", "Best Picks vs"]:
                if wr_list is None:
                    try:
                        wr_list = self._find_list_container_by_header(driver, header_prefix)
                    except Exception:
                        pass

            # Structural fallback: find three-column grid under #content and use columns 2 (WR) and 3 (GD15)
            if gd_list is None or wr_list is None:
                try:
                    grid = driver.find_element(By.XPATH, "//div[@id='content']//div[contains(@class,'grid')][.//a[contains(@class,'items-center')]]")
                    cols = grid.find_elements(By.XPATH, ".//div[contains(@class,'grid')]/div | :scope>div")
                except Exception:
                    cols = []
                if gd_list is None and len(cols) >= 3:
                    try:
                        gd_list = cols[2].find_element(By.XPATH, ".//div[contains(@class,'overflow-auto')] | .")
                    except Exception:
                        pass
                if wr_list is None and len(cols) >= 2:
                    try:
                        wr_list = cols[1].find_element(By.XPATH, ".//div[contains(@class,'overflow-auto')] | .")
                    except Exception:
                        pass

            # Fallback: wait for at least one row anywhere if neither list was found quickly
            if gd_list is None and wr_list is None:
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((
                    By.XPATH, "//a[contains(@class,'items-center')]"
                )))
                # Content-based fallback: find rows by right-hand cell text patterns
                try:
                    wr_rows = driver.find_elements(By.XPATH, "//a[contains(@class,'items-center')][./div[3]//div[contains(text(), '% WR')]]")
                    if wr_rows:
                        wr_list = driver
                except Exception:
                    pass
                try:
                    gd_rows = driver.find_elements(By.XPATH, "//a[contains(@class,'items-center')][./div[3]//div[contains(text(), ' GD15')]]")
                    if gd_rows:
                        gd_list = driver
                except Exception:
                    pass

            # If using content-based fallback, scope WR/GD to first matching container only
            # (wr_list/gd_list set to driver indicates global search; we'll resolve the first parent container)

            if gd_list is not None:
                if gd_list is driver:
                    # Resolve to the first parent container of a GD15 row
                    try:
                        first_gd_row = driver.find_element(By.XPATH, "//a[contains(@class,'items-center')][./div[3]//div[contains(text(), ' GD15')]]")
                        gd_list = first_gd_row.find_element(By.XPATH, "ancestor::div[contains(@class,'overflow-auto')][1]")
                    except Exception:
                        pass
                gd_rows = self._extract_rows(gd_list) if gd_list is not driver else driver.find_elements(By.XPATH, "//a[contains(@class,'items-center')][./div[3]//div[contains(text(), ' GD15')]]")
                print(f"    Found {len(gd_rows)} GD15 rows")
                for row in gd_rows:
                    counter_champ, gd15, games = self._parse_gd15_row(row)
                    self.ngames[role].update_matchup(champion, counter_champ, games)
                    self.gold_diff[role].update_matchup(champion, counter_champ, gd15)
            else:
                print("    GD15 list not found via header or structure fallback")

            if wr_list is not None:
                if wr_list is driver:
                    # Resolve to the first parent container of a WR row to avoid both WR columns
                    try:
                        first_wr_row = driver.find_element(By.XPATH, "//a[contains(@class,'items-center')][./div[3]//div[contains(text(), '% WR')]]")
                        wr_list = first_wr_row.find_element(By.XPATH, "ancestor::div[contains(@class,'overflow-auto')][1]")
                    except Exception:
                        pass
                wr_rows = self._extract_rows(wr_list) if wr_list is not driver else driver.find_elements(By.XPATH, "//a[contains(@class,'items-center')][./div[3]//div[contains(text(), '% WR')]]")
                print(f"    Found {len(wr_rows)} WR rows (pre-dedupe)")
                seen = set()
                kept = []
                for row in wr_rows:
                    try:
                        name = row.find_element(By.XPATH, "./div[2]//div[contains(@class,'font-bold')]").text
                    except Exception:
                        name = None
                    if name and name not in seen:
                        seen.add(name)
                        kept.append(row)
                print(f"    Kept {len(kept)} WR rows after de-dup")
                for row in kept:
                    counter_champ, wr, games = self._parse_wr_row(row)
                    self.winrate[role].update_matchup(champion, counter_champ, wr)
            else:
                print("    WR list not found via header or structure fallback")

        except Exception as e:
            print(f"Error processing {champion} {role}: {str(e)}")

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import numpy as np
import urllib, json
from datetime import date, timedelta, datetime

# # Set up Chrome options
# chrome_options = Options()
# # chrome_options.add_argument("--headless")  # Uncomment this if you want to run in headless mode
# chrome_options.add_argument("--window-size=1920,1080")

# # Initialize the driver
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# try:
#     # Get the page
#     url = "https://u.gg/lol/champions/riven/counter"
#     driver.get(url)

#     # Wait for the consent button to be clickable and click it
#     consent_button = WebDriverWait(driver, 30).until(
#         EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'fc-cta-consent')]"))
#     )
#     consent_button.click()

#     # Wait for the "See More Champions" button to be clickable and click it
#     see_more_button = WebDriverWait(driver, 30).until(
#         EC.element_to_be_clickable((By.XPATH, "//div[text()='See More Champions']"))
#     )
#     see_more_button.click()


#     # Extract champion names from hrefs
#     champions = []
#     counters_container = driver.find_element(By.CLASS_NAME, "counters-container")
#     third_column = counters_container.find_elements(By.CLASS_NAME, "counters-column")[2]
#     champion_cards = third_column.find_elements(By.CLASS_NAME, "counter-list-card")
    
#     gold_diffs = np.array([(c.find_elements(By.CLASS_NAME, "champion-name")[0].text,int(c.find_elements(By.CLASS_NAME, "win-rate")[0].text.split(" ")[0]),int(c.find_elements(By.CLASS_NAME, "total-games")[0].text.split(" ")[0].replace(",",""))) for c in champion_cards])
# finally:
#     driver.quit()

versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
with urllib.request.urlopen(versions_url) as url:
    versions = json.load(url)
    version = versions[0]
champion_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"

with urllib.request.urlopen(champion_url) as url:
    champ_json = json.load(url)

champ_dict = {}
for i,champ_name in enumerate(champ_json['data']):
    if champ_name.replace(' ','').lower() == 'monkeyking':
        champ_name = "wukong"
    champ_dict[f"{champ_name.replace(' ','').lower()}"] = i

myStats = gameStats(champ_dict, "create")
pass