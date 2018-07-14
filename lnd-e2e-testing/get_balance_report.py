#!/usr/bin/python3

import subprocess
import json
import sys

date = subprocess.check_output(["date", "-Iminutes"]).decode("utf-8").strip()
wallet_balance = json.loads(subprocess.check_output(["lncli", "walletbalance"]).decode("utf-8"))
channel_balance = json.loads(subprocess.check_output(["lncli", "channelbalance"]).decode("utf-8"))
chain_txns = json.loads(subprocess.check_output(["lncli", "listchaintxns"]).decode("utf-8"))["transactions"]

wallet = int(wallet_balance["confirmed_balance"])
wallet_unconfirmed = int(wallet_balance["unconfirmed_balance"])
channel = int(channel_balance["balance"])
pending = int(channel_balance["pending_open_balance"])
total = wallet + wallet_unconfirmed + pending + channel
chain_fees = sum([int(i["total_fees"]) for i in chain_txns])

if len(sys.argv) < 2 or sys.argv[1] != '--no-header':
    print(
      "Time\t\t\t"
      "Wallet\t\t"
      "Unconfirmed\t"
      "Pending\t\t"
      "Channel\t\t"
      "ChainFees\t\t"
      "Total"
    )

print(
  date + \
  "\t{:,}".format(wallet) + \
  "\t{:,}".format(wallet_unconfirmed) + \
  "\t{:,}".format(pending) + \
  "\t{:,}".format(channel) + \
  "\t{:,}".format(chain_fees) + \
  "\t{:,}".format(total)
)

# Setup:
# chmod +x ~/lnd-e2e-testing/get_balance_report.py
# ~/lnd-e2e-testing/get_balance_report.py > ~/balance_history.tab
# corntab -e  # cron job to record balance every hour:
# 0 *  *   *   *     ~/lnd-e2e-testing/get_balance_report.py --no-header >> ~/balance_history.tab

# Check balance:
# (cat ~/balance_history.tab; ~/lnd-e2e-testing/get_balance_report.py | sort) | column -t
#
# Example Output:
# Time                   Wallet       Unconfirmed  Pending    Channel      ChainFees  Total
# 2018-07-12T20:18-0700  154,430,415  0            0          124,546,659  71,093     278,977,074
# 2018-07-13T07:36-0700  153,211,432  0            0          123,710,571  74,055     276,922,003
# 2018-07-13T07:58-0700  144,057,139  9,152,804    3,221,709  119,914,308  75,177     273,124,251
