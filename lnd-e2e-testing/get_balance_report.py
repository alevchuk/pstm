#!/usr/bin/python3

import subprocess
import json
import sys

date = subprocess.check_output(["date", "-Iminutes"]).decode("utf-8").strip()
wallet_balance = json.loads(subprocess.check_output(["lncli", "walletbalance"]).decode("utf-8"))
channel_balance = json.loads(subprocess.check_output(["lncli", "channelbalance"]).decode("utf-8"))

wallet = int(wallet_balance["confirmed_balance"])
wallet_unconfirmed = int(wallet_balance["unconfirmed_balance"])
channel = int(channel_balance["balance"])

if sys.argv[1] == '--json':
    print(json.dumps({
      'wallet': "{:,}".format(wallet),
      'unconfirmed': "{:,}".format(wallet_unconfirmed),
      'channel': "{:,}".format(channel),
      'total': "{:,}".format(wallet + wallet_unconfirmed + channel)}, sort_keys=True))
else:
    print(
      date + \
      "\t" "{:,}".format(wallet) + \
      "\t" "{:,}".format(wallet_unconfirmed) + \
      "\t" + "{:,}".format(channel) + \
      "\t" + "{:,}".format(wallet + wallet_unconfirmed + channel))

# Setup:
# chmod +x ~/mytoolz/get_balance_report.py
# echo -e "Time\tWallet\tUnconfirmed\tChannel\tTotal" >> ~/balance_history.tab

# Update balance:
# ~/mytoolz/get_balance_report.py  >> ~/balance_history.tab

# Check balance:
# (cat ~/balance_history.tab; ~/mytoolz/get_balance_report.py) | column -t
#
# Example Output:
#                        Wallet  Unconfirmed  Channel     Total
# 2018-01-14T16:14-0800  0       176,958,526  33,547,192  210,505,718
# 2018-01-14T16:55-0800  0       143,399,817  50,329,476  193,729,293
# 2018-01-14T16:55-0800  0       143,399,817  50,329,476  193,729,293
