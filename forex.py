import requests
from bs4 import BeautifulSoup
import json
import datetime

EMOJI = {
    "EUR": "🇪🇺",
    "GBP": "🇬🇧",
    "CAD": "🇨🇦",
    "AUD": "🇦🇺", 
    "JPY": "🇯🇵",
    "CHF": "🇨🇭",
    "IRR": "🇮🇷",
    "BRL": "🇧🇷",
    "RUB": "🇷🇺",
    "ZAR": "🇿🇦",
    "CNY": "🇨🇳",
    "USDT": "crypto",
    "BTC": "crypto",
    "ETH": "crypto",
    "BNB": "crypto"
}

# Iranian Rial
def get_USDIRR():
    # request
    url = 'https://www.tgju.org/currency'
    response = requests.get(url)
    parsed_html = BeautifulSoup(response.text, "html.parser")

    # find currency price
    USDIRR = parsed_html.body.find(attrs={"data-market-row": "price_dollar_rl"})
    value = USDIRR['data-price']
    value = round(float(value.replace(',', '')), 6)

    return value

def get_USDother():
    # request
    url = 'https://www.freeforexapi.com/api/live?pairs=EURUSD,GBPUSD,USDCAD,AUDUSD,USDJPY,USDCHF,USDZAR'
    response = requests.get(url)
    parsed_json = json.loads(response.text)

    # get ratess
    USDETC = {}
    for pair in parsed_json['rates']:
        # pair already has correct conversion
        if(pair.startswith('USD')):
            USDETC[pair] = parsed_json['rates'][pair]['rate']
        else:
            # change ETCUSD to USDETC
            USDETC[pair[3:] + pair[:3]] = round(1.0 / parsed_json['rates'][pair]['rate'], 6)

    return USDETC

def get_yahoorate_USD(cur):
    # requests
    url = f'https://finance.yahoo.com/quote/{cur}=X/'
    # header necessary for yahoo otherwise they will block the request with a 404
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    parsed_html = BeautifulSoup(response.text, "html.parser")

    # find currency price
    value = parsed_html.find(attrs={"data-test": "BID-value"}).string
    
    return value

def get_yahoorate_crypto(cur):
    # requests
    url = f'https://finance.yahoo.com/quote/{cur}-USD'
    # header necessary for yahoo otherwise they will block the request with a 404
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    parsed_html = BeautifulSoup(response.text, "html.parser")

    # find currency price
    value = parsed_html.find(attrs={"data-test": "qsp-price"}).string
    value = value.replace(",", "")
    
    return float(value)



def main():
    for key, value in EMOJI.items():
        if key == "IRR":
            print(f"🇺🇸\tto\t{value} \t {get_USDIRR()}")
        else:
            print(f"🇺🇸\tto\t{value} \t {get_yahoorate_USD(key)}")