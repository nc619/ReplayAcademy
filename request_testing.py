import requests

r = requests.get("https://127.0.0.1:2999/replay/render", verify="riotgames.pem")
cameraData = {'banners': True}
r1=requests.post("https://127.0.0.1:2999/replay/render", verify="riotgames.pem",data=cameraData)
pass

blue_fountain = {'x': 235, 'y': 300, 'z': 260}
red_fountain = {'x': 14500, 'y': 300, 'z': 14500}
top_position = {'cameraRotation': {'x': 225, 'y': 85,'z': 0}}
top_position['cameraPosition'] = {}
for key in blue_fountain:
    top_position['cameraPosition'][key] = (red_fountain[key]-blue_fountain[key])/2-blue_fountain
top_position = {'cameraPosition': {'x': 14250, 'y': 22000, 'z': 14250/2-200}, 'cameraRotation': {'x': 225, 'y': 85,'z': 0}}
