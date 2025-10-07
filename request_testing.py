# import requests

# r = requests.get("https://127.0.0.1:2999/replay/render", verify="riotgames.pem")
# cameraData = {'banners': True}
# r1=requests.post("https://127.0.0.1:2999/replay/render", verify="riotgames.pem",data=cameraData)
# pass

# blue_fountain = {'x': 235, 'y': 300, 'z': 260}
# red_fountain = {'x': 14500, 'y': 300, 'z': 14500}
# top_position = {'cameraRotation': {'x': 225, 'y': 85,'z': 0}}
# top_position['cameraPosition'] = {}
# for key in blue_fountain:
#     top_position['cameraPosition'][key] = (red_fountain[key]-blue_fountain[key])/2-blue_fountain
# top_position = {'cameraPosition': {'x': 14250, 'y': 22000, 'z': 14250/2-200}, 'cameraRotation': {'x': 225, 'y': 85,'z': 0}}

# Fetch the document content as HTML
import requests
from bs4 import BeautifulSoup
import numpy as np

def get_rows(url):
    # This function gets the data from the url and parses it into a list of rows (non readable yet)
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find_all('table')
        rows = table.find_all('tr')
        return rows
    else:
        raise(f"Failed to retrieve the document. Status code: {response.status_code}")

def create_grid(rows):
    # This function takes the rows and reads the text data from each row
    # and transforms the table from the url into a 2d array
    # Then it creates the text grid from the 2d array which already looks like the letters
    # When creating this, it takes into account the convention of the docs so that the array looks good
    grid = []
    for row in rows:
        cells = row.find_all(['th', 'td'])
        cell_values = [cell.get_text(strip=True) for cell in cells]
        grid.append(cell_values)
    grid_array = np.array(grid)
    out_grid = np.full((np.array(grid_array[1:,-1],dtype=int).max()+1,np.array(grid_array[1:,0],dtype=int).ma x()+1),' ')
    for i in range(1,grid_array.shape[0]):
        c_i = int(grid_array[i,0])
        r_i = out_grid.shape[0]-1-int(grid_array[i,-1])
        out_grid[r_i,c_i] = grid_array[i,1]        
    return out_grid

def print_grid(grid):
    # This function prints the final grid into text, just by using join to join
    # the elements of al ine together and prints them one by one
    # No need to add "\n" because the join function already does that
    for i in range(grid.shape[0]):
        print(''.join(grid[i]))

def run(url):
    # Runs everything
    rows = get_rows(url)
    grid = create_grid(rows)
    print_grid(grid)
    
    
url = "https://docs.google.com/document/d/e/2PACX-1vSHesOf9hv2sPOntssYrEdubmMQm8lwjfwv6NPjjmIRYs_FOYXtqrYgjh85jBUebK9swPXh_a5TJ5Kl/pub"
run(url)
# # Check if the request was successful
# if response.status_code == 200:
#     # Parse the HTML content with BeautifulSoup
#     soup = BeautifulSoup(response.content, 'html.parser')

#     # Find all tables in the document
#     tables = soup.find_all('table')

#     # Iterate through each table
#     for table_idx, table in enumerate(tables):
#         print(f"\nTable {table_idx + 1}:")
        
#         # Get all rows in the table
#         rows = table.find_all('tr')
        
#         for row in rows:
#             # Get all cells in the row (both 'th' and 'td')
#             cells = row.find_all(['th', 'td'])
#             cell_values = [cell.get_text(strip=True) for cell in cells]
            
#             # Print the row values
#             print('\t'.join(cell_values))
# else:
#     print(f"Failed to retrieve the document. Status code: {response.status_code}")