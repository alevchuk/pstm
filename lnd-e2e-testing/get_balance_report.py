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
pending = int(channel_balance["pending_open_balance"])

if len(sys.argv) > 1 and sys.argv[1] == '--json':
    print(json.dumps({
      'wallet': "{:,}".format(wallet),
      'unconfirmed': "{:,}".format(wallet_unconfirmed),
      'pending': "{:,}".format(pending),
      'channel': "{:,}".format(channel),
      'total': "{:,}".format(wallet + wallet_unconfirmed + pending + channel)}, sort_keys=True))
else:
    print(
      "Time\t\t\t"
      "Wallet\t\t"
      "Unconfirmed\t"
      "Pending\t\t"
      "Channel\t\t"
      "Total")
    print(
      date + \
      "\t{:,}".format(wallet) + \
      "\t{:,}".format(wallet_unconfirmed) + \
      "\t{:,}".format(pending) + \
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
# Time                   Wallet       Unconfirmed  Pending  Channel      Total
# 2018-07-04T10:52-0700  142,761,249  0            -        198,204,893  340,966,142
# 2018-07-04T15:58-0700  136,241,507  8,330,263    -        92,415,232   236,987,002
# 2018-07-04T21:03-0700  130,980,127  0            -        188,390,196  319,370,323
