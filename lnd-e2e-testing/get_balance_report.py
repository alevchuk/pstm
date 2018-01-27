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

if len(sys.argv) > 1 and sys.argv[1] == '--json':
    print(json.dumps({
      'wallet': "{:,}".format(wallet),
      'unconfirmed': "{:,}".format(wallet_unconfirmed),
      'channel': "{:,}".format(channel),
      'total': "{:,}".format(wallet + wallet_unconfirmed + channel)}, sort_keys=True))
else:
    print(
      "Time\t\t\t"
      "Wallet\t\t"
      "Unconfirmed\t"
      "Channel\t\t"
      "Total")
    print(
      date + \
      "\t{:,}".format(wallet) + \
      "\t{:,}".format(wallet_unconfirmed) + \
      "\t{:,}".format(channel) + \
      "\t{:,}".format(wallet + wallet_unconfirmed + channel))

# Setup:
# chmod +x ~/lnd-e2e-testing/get_balance_report.py
# ~/lnd-e2e-testing/get_balance_report.py > ~/balance_history.tab

# Update balance:
# ~/lnd-e2e-testing/get_balance_report.py | grep -v Time  >> ~/balance_history.tab

# Check balance:
# (cat ~/balance_history.tab; ~/lnd-e2e-testing/get_balance_report.py | sort) | column -t
#
# Example Output:
#                        Wallet  Unconfirmed  Channel     Total
# 2018-01-14T16:14-0800  0       176,958,526  33,547,192  210,505,718
# 2018-01-14T16:55-0800  0       143,399,817  50,329,476  193,729,293
# 2018-01-14T16:55-0800  0       143,399,817  50,329,476  193,729,293
