import requests

url = 'http://127.0.0.1:5000/ohlc/APPL'
response = requests.get(url)
print(response.json())
