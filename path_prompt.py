from tkinter import Tk
from tkinter.filedialog import askopenfilename
import os, pathlib
    
try: 
    pre_path = f"{pathlib.Path.home().drive}/Riot Games/League of Legends/Config/game.cfg"
    path = askopenfilename(filetypes = [('Config Files', '.cfg')], initialfile=pre_path, initialdir=pre_path, title = 'Select Riot Games\League of Legends\Config\game.cfg')
except: 
    path = askopenfilename(filetypes = [('Config Files', '.cfg')], title = 'Select Riot Games\League of Legends\Config\game.cfg')

# Open the file in read mode and read all lines
with open(path, "r") as f:
    lines = f.readlines()

# Iterate over the lines and replace as necessary
for i, line in enumerate(lines):
    if "EnableReplayApi=" in line:
        if "EnableReplayApi=0" in line:
            lines[i] = "EnableReplayApi=1\n"
        # else:
            # lines[i] = "EnableReplayApi=1\n"

# Open the file in write mode and write the modified lines
with open(path, "w") as f:
    f.writelines(lines)




# with open(path, "") as f:
#     for line in f:
#         print(line)
#         if "EnableReplayApi=" in line:
#             print(line)
#             if "EnableReplayApi=1" in line:
#                 line = "EnableReplayApi=1"
#             else:
#                 line = "EnableReplayApi=0"
#         f.write(line)