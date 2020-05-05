primary_node_url = "http://nodes.neutrino.at"
fallback_node_url = "http://nodes.wavesnodes.com"

# fill with your channels' ids
chat_ids = {
"main_channel":"",
"test_channel":""
}

# insert your bot api
bot_api_key = ""

chat = chat_ids.get("test_channel")

get_transactions_amount = 25

seconds_between_requests = 7

status_update_max = 1500

control_contract = "3P5Bfd58PPfNvBM2Hy8QfbcDqMeNtzg7KfP"

contracts = ["3PC9BfRwJWWiw9AREE2B3eWzCks3CYtg4yo",
                    "3PG2vMhK5CPqsCDodvLGzQ84QkoHXCJ3oNP",
                    "3P5Bfd58PPfNvBM2Hy8QfbcDqMeNtzg7KfP",
                    "3P4PCxsJqMzQBALo8zANHtBDZRRquobHQp7",
                    "3PNikM6yp4NqcSU8guxQtmR5onr2D4e8yTJ"]

critical_triggers = [{"type_id": 13, "type_string": "'Script Update'", "status": "CRITICAL ALERT"},
                     {"type_id": 12, "type_string": "'Data'", "status": "CRITICAL ALERT"}]
test_triggers = [{"type_id": 16, "type_string": "'Invoke script transaction'", "status": "NORMAL"}]


finalize_price_check_delta = 10
