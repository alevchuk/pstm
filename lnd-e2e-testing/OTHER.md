Pay Between Node A and Node B back and forth
=============================================

For an end-to-end test you may want to use this ping-pong type of setup between node A and node B. Node A will issue micropayments to node B until it can't (ran out to funds or run out of channels). After 10 minutes of "can't" A and B switch roles. B starts paying A until it can't. And so on ...

This can also help testnet generate some payment traffic so we can test multihop routing.

```
# Do this on both A and B
mkdir ~/lnd-e2e-testing/
cd ~/lnd-e2e-testing/
curl https://raw.githubusercontent.com/alevchuk/pstm/master/lnd-e2e-testing/get_balance_report.py > ./get_balance_report.py
curl https://raw.githubusercontent.com/alevchuk/pstm/master/lnd-e2e-testing/pay_or_get_paid.py > ./pay_or_get_paid.py
chmod +x ./get_balance_report.py
chmod +x ./pay_or_get_paid.py

# On A start the server (port 5867 needs to be reachable by node B)
 ~/lnd-e2e-testing/pay_or_get_paid.py -l -p 5867
 
 # On B start the client
 ~/lnd-e2e-testing/pay_or_get_paid.py -s <IP of node A> -p 5867
```



Monitor number of Active Channels
=================================
```
while :; do 
  echo "$(date) $(lncli listchannels  | grep '"active": true,' | sort | uniq -c)"; sleep 60; done
```

Close All Channels
==================

This may be needed during backward incombatible upgrades of LND. Then you need to close all the channels before upgrading.

1. Restart LND with autopilot disabled.
2. Run
```
lncli listchannels | grep '"active": true' -A 2 | awk -F'"' '/point/ {print $4}' | while read cp; do 
  funding_txn=$(echo $cp | awk -F: '{print $1}');
  output_index=$(echo $cp | awk -F: '{print $2}'); 
  lncli closechannel $funding_txn --output_index $output_index; done
```
3. For uncooperative close, add **-f** to  `lncli closechannel` 

Close All Channels with no Remote Balance
=========================================

This can help if your trying to maximize your chances of being a relay. With no Remote Balance there is nothing to relay.

```
lncli listchannels | grep '"remote_balance": "0"' -B 10  | \
grep '"active": true' -A 2 | awk -F'"' '/point/ {print $4}' | sort -R | while read cp; do
  funding_txn=$(echo $cp | awk -F: '{print $1}');
  output_index=$(echo $cp | awk -F: '{print $2}');
  lncli closechannel $funding_txn --output_index $output_index; done

# Now monitor you active channels
while :; do lncli listchannels | grep '"active": true' -A 10 | grep remote_balance | tr -d '"' | sort -n -k2; echo; sleep 1; done
```


Pay Invoice Retry
=================

On testnet the graph is not well connected, so as you add more channels to get connectivity, you may need to keep retying to pay an invoice. 

1. Side A: Create an invoice with longer expiry (default expiry is 1 hour, here 5867 is the requested amount in Satoshi):
```
lncli addinvoice --expiry $((3600 * 24)) 5867
```

2. Side B: Re-try until successful (get <pay_req> from step 1):
```
while :; do time lncli payinvoice <pay_req> || break; sleep 60; done
```

