import requests

ticker = input("Request a Ticker:")
url = 'http://127.0.0.1:5000/ohlc/'+ticker
answer = input("Would you like to Reqeust Specific Time Range (y/n): ").lower()

if answer=="y" or answer == "yes":
    print("Example Format: 2024-01-01")
    startTime = input("Request a Start Time: ")
    endTime = input("Request an End Time: ")
    url += '?start_date=' + startTime + '&end_date='+ endTime 
    print(url)
# http://127.0.0.1:5000/ohlc/AAPL?start_date=2022-01-01&end_date=2022-03-01
else:
    print(url)
