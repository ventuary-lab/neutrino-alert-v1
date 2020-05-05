import requests
import time
from datetime import datetime, timedelta
import config as cfg

# Global variables
global NODE_URL
NODE_URL = cfg.primary_node_url
CHAT_ID = cfg.chat
SECONDS_BETWEEN_REQS = cfg.seconds_between_requests
STATUS_UPDATE_MAX = cfg.status_update_max
STATUS_UPDATE_COUNTER = STATUS_UPDATE_MAX
CONTRACT_ADDRESSES = cfg.contracts
CONTROL_CONTRACT = cfg.control_contract
GET_TRANSACTIONS_AMOUNT = cfg.get_transactions_amount

session = requests.Session()
session.verify = True

def get_transactions_batch(contract_list):
    try:
        print("Executing 'get_transactions_batch'...")
        response = []
        for i in contract_list:
            new_response = session.get(
                url=f'{NODE_URL}/transactions/address/{i}/limit/{str(GET_TRANSACTIONS_AMOUNT)}',
                params={})

            if new_response:
                response += new_response.json()[0]
            else:
                print("Response is NoneType.")
                send_alert_to_tg("[...] SERVICE ERROR: the node returned invalid response, unable to get last transactions. Please check logs.",CHAT_ID)
        return response
    except Exception as e:
        print(e)
        send_alert_to_tg(
            "[...] SERVICE ERROR: An error has occurred in 'get_transactions_batch'. Please check logs.\n\n" + str(e),
            CHAT_ID)


def simple_transaction_alert(transaction, triggers):
    try:
        print("Executing 'simple_transaction_alert'...")
        for trigger in triggers:
            if transaction["type"] == trigger["type_id"]:
                res_string = "[!!!] " + trigger["status"] + "\n"
                res_string += "Transaction Type: " + trigger["type_string"] + "\n"
                res_string += "Check here: " + "wavesexplorer.com/tx/" + transaction['id'] + "\n"
                send_alert_to_tg(res_string, CHAT_ID)
    except Exception as e:
        print(e)
        send_alert_to_tg(
            "[...] SERVICE ERROR: An error has occurred in 'simple_transaction_alert'. Please check logs.\n" + str(e),
            CHAT_ID)

def shutdown_alert():
    try:
        print("Executing 'shutdown_alert'...")
        control_contract_address = cfg.control_contract

        isBlocked = session.get(url=f'{NODE_URL}/addresses/data/{control_contract_address}/is_blocked',
                                params={}).json()

        print("isBlocked? ",isBlocked)

        if isBlocked.get('error') == 304:
            return
        elif isBlocked.get('value') == True:
            isBlockedCaller = session.get(
                url=f'{NODE_URL}/addresses/data/{control_contract_address}/is_blocked_caller',
                params={}).json()
            isBlockedReason = session.get(
                url=f'{NODE_URL}/addresses/data/{control_contract_address}/is_blocked_reason',
                params={}).json()
            send_alert_to_tg(f'[!!!] CRITICAL ALERT: SC has been shut down! \n Caller address: {str(isBlockedCaller.get("value"))}\n Reason: {str(isBlockedReason.get("value"))}', CHAT_ID)

        global CHECK_SHUTDOWN_LAST_TIME
        CHECK_SHUTDOWN_LAST_TIME = datetime.now()
    except Exception as e:
        print(e)
        send_alert_to_tg("[...] SERVICE ERROR: An error has occurred in 'shutdown_alert'. Most likely the Node is not responding. Please check logs.\n" + str(e), CHAT_ID)

def transfer_alert(transaction):
    try:
        print("Executing 'transfer_alert'...")
        transfer_triggers = [{"type_id": 11, "type_string": "'Mass Transfer'", "status": "CRITICAL"},
                             {"type_id": 4, "type_string": "'Transfer'", "status": "CRITICAL"}]
        for trigger in transfer_triggers:
            if (transaction["type"] == trigger["type_id"]) and (transaction["sender"] in CONTRACT_ADDRESSES):
                res_string = "Alert Status: " + trigger["status"] + "\n"
                res_string += "Transaction Type: " + trigger["type_string"] + "\n"
                res_string += "Check here: " + "wavesexplorer.com/tx/" + transaction['id'] + "\n"
                send_alert_to_tg(res_string, CHAT_ID)
    except Exception as e:
        print(e)
        send_alert_to_tg("[...] SERVICE ERROR: An error has occurred in 'simple_transaction_alert'. Most likely the Node is not responding. Please check logs.\n" + str(e), CHAT_ID)


def send_alert_to_tg(alert, CHAT_ID):
    try:
        print("Executing 'send_alert_to_tg'...")
        bot_api_key = cfg.bot_api_key
        DATA = {"chat_id": CHAT_ID, "text": alert}
        requests.post(url="https://api.telegram.org/bot%s/sendMessage" % (bot_api_key), data=DATA)
    except Exception as e:
        print(e)
        send_alert_to_tg("[...] SERVICE ERROR: An error has occurred in 'send_alert_to_tg'. Could not send message. Please check logs.\n" + str(e),
                         CHAT_ID)


def update_price_alert(transaction):
    try:
        print("Executing 'update_price_alert'...")
        if "call" in transaction.keys():
            if transaction["call"]["function"] == 'finalizeCurrentPrice':
                global FINALIZE_PRICE_LAST_TIME
                FINALIZE_PRICE_LAST_TIME = datetime.now()

                global THERE_WAS_A_PRICE_GAP
                if THERE_WAS_A_PRICE_GAP:
                    send_alert_to_tg("[...] MESSAGE: The price has finally been updated!\n---------------------------------------", CHAT_ID)
                    THERE_WAS_A_PRICE_GAP = False

    except Exception as e:
        print(e)
        send_alert_to_tg(
            "[...] SERVICE ERROR: An error has occurred in 'update_price_alert'. Please check logs.\n" + str(e), CHAT_ID)


def get_last_height():
    try:
        return session.get(url=f'{NODE_URL}/blocks/height').json()['height']
    except Exception as e:
        print(e)
        send_alert_to_tg("[...] SERVICE ERROR: An error has occurred in 'get_last_height'. Please check logs.\n" + str(e),
                         CHAT_ID)


def check_price_delta(delta):
    try:
        print("Executing 'check_price_delta'...")
        control_contract_address = cfg.control_contract

        last_height = get_last_height()
        last_price = session.get(url=f'{NODE_URL}/addresses/data/{control_contract_address}',
                                params={'key':'price'}).json()[0]['value']
        print("Last price is:", last_price)
        all_data = session.get(url=f'{NODE_URL}/addresses/data/{control_contract_address}',
                                params={'matches':'price\_[0-9]*'}).json()

        delta_formatted = str(delta // 60)
        delta_blocks = last_height - delta

        price_delta_ago = [element for element in all_data if element['key'] == ('price_' + str(delta_blocks))]
        while True:
            if len(price_delta_ago) > 0:
                break
            else:
                delta_blocks -= 1
                price_delta_ago = [element for element in all_data if element['key'] == ('price_' + str(delta_blocks))]

        price_delta_ago = price_delta_ago[0]['value']
        price_difference_in_percent = (abs(last_price - price_delta_ago) / ((last_price + price_delta_ago) / 2)) * 100
        if price_difference_in_percent > 5:
            response = f'[...] WARNING: {delta_formatted} hour(s) ago, the price was >5% different. More info:\nLast ' \
                       f'block height: {last_height} \nLast price: {last_price} \nPrice {delta_formatted} ho' \
                       f'ur(s) ago: {price_delta_ago} \nPrice difference (per cent): {price_difference_in_percent} '
            send_alert_to_tg(response, CHAT_ID)

        global CHECK_PRICE_DELTA_LAST_TIME
        CHECK_PRICE_DELTA_LAST_TIME = datetime.now()
    except Exception as e:
        print(e)
        send_alert_to_tg("[...] SERVICE ERROR: An error has occurred in 'check_price_delta'. Please check logs.\n" + str(e), CHAT_ID)


if __name__ == "__main__":
    try:
        send_alert_to_tg("[...] MESSAGE: Bot is restarting.", CHAT_ID)

        # First time counter triggers
        CHECK_PRICE_DELTA_LAST_TIME = datetime.now()
        FINALIZE_PRICE_LAST_TIME = datetime.now()
        CHECK_SHUTDOWN_LAST_TIME = datetime.now()

        LAST_HEIGHT = get_last_height()
        print("First price update check time is: ", FINALIZE_PRICE_LAST_TIME)
        THERE_WAS_A_PRICE_GAP = False

        print("Getting first Transaction snapshot...")
        FIRST_SNAP = get_transactions_batch(CONTRACT_ADDRESSES)

        send_alert_to_tg("[...] MESSAGE: Running initial price check...", CHAT_ID)
        check_price_delta(60)
        check_price_delta(60 * 2)
        check_price_delta(60 * 5)

        send_alert_to_tg("[...] MESSAGE: Running initial shutdown check...", CHAT_ID)
        shutdown_alert()
        send_alert_to_tg("[...] MESSAGE: Initial shutdown check executed, continuing operation.", CHAT_ID)


    except Exception as e:
        print(e)
        send_alert_to_tg("[...] BOT ERROR: An error has occurred in the main block. Please check logs.\n" + str(e),
                         CHAT_ID)

    while True:
        try:
            time.sleep(SECONDS_BETWEEN_REQS)

            if CHECK_PRICE_DELTA_LAST_TIME + timedelta(minutes=40) < datetime.now():
                check_price_delta(60)
                check_price_delta(60 * 2)
                check_price_delta(60 * 3)

            if FINALIZE_PRICE_LAST_TIME + timedelta(minutes=cfg.finalize_price_check_delta) < datetime.now():
                print(LAST_HEIGHT, get_last_height())
                if LAST_HEIGHT < get_last_height():
                    send_alert_to_tg("[...] WARNING: No finalizeCurrentPrice has taken place for 10 minutes or more!",
                                     CHAT_ID)
                    LAST_HEIGHT = get_last_height()
                    THERE_WAS_A_PRICE_GAP = True

            if CHECK_SHUTDOWN_LAST_TIME + timedelta(minutes=3) <datetime.now():
                shutdown_alert()


            critical_triggers = [{"type_id": 13, "type_string": "'Script Update'", "status": "CRITICAL ALERT"},
                                 {"type_id": 12, "type_string": "'Data'", "status": "CRITICAL ALERT"}]
            test_triggers = [{"type_id": 16, "type_string": "'Invoke script transaction'", "status": "NORMAL"}]

            time.sleep(SECONDS_BETWEEN_REQS)
            next_snap = get_transactions_batch(CONTRACT_ADDRESSES)
            new_transactions = []
            new_transactions = [i for i in next_snap if i not in FIRST_SNAP]

            FIRST_SNAP = next_snap
            if not new_transactions:
                print("Contracts checked. No new transactions.")
            else:
                print("New ", len(new_transactions), " transaction(s) detected: ", new_transactions)
                for transaction in new_transactions:
                    simple_transaction_alert(transaction, critical_triggers)
                    update_price_alert(transaction)
                    transfer_alert(transaction)
                new_transactions = []

            STATUS_UPDATE_COUNTER -= 1
            if STATUS_UPDATE_COUNTER < 0:
                send_alert_to_tg(
                    "[...] MESSAGE: " + str(STATUS_UPDATE_MAX) + " checks have passed. Bot is operating normally.",
                    CHAT_ID)
                STATUS_UPDATE_COUNTER = STATUS_UPDATE_MAX

        except Exception as e:
            print(e)
            send_alert_to_tg("[...] BOT ERROR: An error has occurred in the while loop. Please check logs.", CHAT_ID)