import forex
import requests
import json
from argparse import ArgumentParser
import time
from datetime import datetime, timezone

'''
simple bot class
'''
class Bot:
    def __init__(self, TOKEN):
        self.url = f"https://api.telegram.org/bot{TOKEN}/"
        self.offset = 0
        self.is_posted = False

    # commands

    def start(self, chat_id):
        message = "Welcome to the USD forex bot. Use the /help command to get a list of functionalities."
        ad = "Please consider joining @usdollartracker for daily updates and more!"
        self.sendMessage(chat_id, message + '\n' + ad)
        return

    def help(self, chat_id):
        message = \
        """Available commands:\n/help: displays a list of available commands\n/getrate <currency code>: displays the exchange rate for <currency code>\n/generalrates: displays general exchange rates for popular currencies converted from US Dollars
        """
        self.sendMessage(chat_id, message)
        return

    def getrate(self, chat_id, currency_code, message_id):
        # currency code check
        rate = None
        result = None
        reply = "Invalid currency code"
        currency_code = currency_code.upper()
        is_crypto = False
        
        # check for IRR
        if currency_code == "IRR":
            rate = forex.get_USDIRR()
            result = f"USD{currency_code} = {rate}"
        # check for other currencies
        else:
            try:
                rate = forex.get_yahoorate_USD(currency_code)
                result = f"USD{currency_code} = {rate}"
            except AttributeError:
                is_crypto = True
            
            # check for crypto
            if is_crypto:
                try:
                    rate = forex.get_yahoorate_crypto(currency_code)
                    result = f"{currency_code}USD = {rate}"
                except Exception as e:
                    self.sendMessage(chat_id, reply, reply_to_message_id=message_id)
                    return
        
        self.sendMessage(chat_id, result)
        return

    def generalrates(self, chat_id):
        message = "Exchange rates for 🇺🇸:\n"
    
        # retrieving general rates from the EMOJI dict
        # crypto currencies contain the value crypto while normal currencies contain the flag emoji
        for key, value in forex.EMOJI.items():
            if key == "IRR":
                message += f"{value} \t USDIRR = {forex.get_USDIRR()}\n"
            elif value == "crypto":
                message += f"{key}USD = \t {forex.get_yahoorate_crypto(key)}\n"
            else:
                message += f"{value} \t USD{key} = {forex.get_yahoorate_USD(key)}\n"

        self.sendMessage(chat_id, message)
        return

    # general bot functions

    def getUpdates(self, offset):
        '''
        gets update by polling
        '''
        try:
            url = self.url + f"getUpdates?offset={offset}"
            response = requests.get(url=url)
            parsed_json = json.loads(response.text)
        except Exception as e:
            print(f"failed to get update with following error: {e}")

        # send the latest update
        return parsed_json
    
    def sendMessage(self, chat_id, text, reply_to_message_id=None):
        '''
        sends a message to a specific chat
        '''
        try:
            url = self.url + "sendMessage"
            params = {
                "chat_id": chat_id,
                "text": text,
                "reply_to_message_id": reply_to_message_id
            }
            response = requests.get(url=url, params=params)
            parsed_json = json.loads(response.text)
        except Exception as e:
            print(f"failed to send message with following error: {e}")

    def forwardMessage(self, chat_id="@usdollartracker", from_chat_id="@usdollartracker", message_id="6"):
        '''
        forwards a message to a specific chat
        '''
        try:
            url = self.url + "forwardMessage"
            params = {
                "chat_id": chat_id,
                "from_chat_id": from_chat_id,
                "message_id": message_id
            }
            response = requests.get(url=url, params=params)
            parsed_json = json.loads(response.text)
        except Exception as e:
            print(f"failed to forward message with following error: {e}")

    def update_channel(self, channel_id="@usdollartracker"):
        '''
        updates a channel with general rate or it forwards the national anthem on saturdays
        '''
        current_time = datetime.now(timezone.utc)
        if current_time.hour == 17 and current_time.minute == 0:
            if not self.is_posted:
                # if saturday forward national anthem
                if current_time.weekday() == 5:
                    text = "Happy Saturday Everyone 😁. No exchange rates today, but listen to the beautiful national anthem of USA! 🇺🇸🇺🇸"
                    self.sendMessage(chat_id="@usdollartracker", text=text)
                    self.forwardMessage()
                else:   
                    self.generalrates(channel_id)

                # set flag true to avoid posting duplcates within the same minute
                self.is_posted = True
        # set is posted back to false once the specified time is passed
        else:
            self.is_posted = False

    def run(self, update):
        '''
        run the bot
        '''
        print(update)
        # get details
        message = update["message"]
        message_id = message["message_id"]
        date = message["date"]
        username = message["from"].get("username")
        first_name = message["from"]["first_name"]
        is_bot = message["from"]["is_bot"]
        chat_id = message["chat"]["id"]
        text = message.get("text")
        entities = message.get("entities")

        # check for non-text type messages
        if text is None:
            reply = "Sorry. I only respond to text messages 😅"
            self.sendMessage(chat_id, text=reply, reply_to_message_id=message_id)
            return
        
        # check for commands
        if text.startswith("/"):

            # get commands
            args = text.split()
            command = args[0]

            if command == "/start":
                self.start(chat_id)
                return
            if command == "/help":
                self.help(chat_id)
                return
            if command == "/generalrates":
                self.sendMessage(chat_id, text="Getting rates...")
                self.generalrates(chat_id)
                return
            if command == "/getrate":
                # find the argument after the command
                currency_code = None
                if len(args) == 1:
                    # there is no argument after command
                    reply = "Did you forget to put an argument after the command?"
                    self.sendMessage(chat_id, text=reply, reply_to_message_id=message_id)
                    return
                else:
                    currency_code = args[1]
                self.getrate(chat_id, currency_code, message_id)
                return
        return

    def poll(self):
        '''
        keeps running the bot and checks for updates
        '''
        print("bot is polling")
        while True:
            time.sleep(1)
            update_id = None
            try:
                # update channel
                self.update_channel()

                # getting the latest updates
                updates = self.getUpdates(self.offset)["result"]

                # no updates
                if not updates:
                    continue
                else:
                    # service first unconfirmed update in the queue [based on Telegram's API]
                    self.run(update=updates[0])

                    # update offset
                    update_id = updates[0]["update_id"]
                    self.offset = update_id + 1

            except Exception as e:
                print(f"failed to poll with following error: {e}")
                # IMPORTANT
                # if you are just starting the bot and it fails, the offset + 1 will not work
                # this is because offset is initiated to 0 until it sees the first update_id
                # make sure the bot is not having any errors on first run
                self.offset = self.offset + 1

    
def main():
    # get token
    parser = ArgumentParser()
    parser.add_argument("-t", "--token", required=True)
    args = parser.parse_args()
    token = args.token

    bot = Bot(token)

    # keep running
    bot.poll()

if __name__ == '__main__':
    main()