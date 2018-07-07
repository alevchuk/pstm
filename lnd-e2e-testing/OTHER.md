Pay back and forth between Node A and Node B 
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

Open many channels
==================

https://github.com/lightningnetwork/lnd/issues/772 **was** a bug in LND.

Check that:
```
lsof -n | grep ^lnd -c
```
shows less than 1k connections (for me this numbers stays as low as 40)


Increase `autopilot.maxchannels`  in `~/.lnd/lnd.conf` and restart LND again
```
autopilot.maxchannels=30
```



Monitor Remote Balance in open Channels
=======================================
```
while :; do date;  lines="$(lncli listchannels  | grep remote_balance | tr -d '"' | sort -n -k2)";  n=$(echo "$lines" | wc -l ); echo "$lines" > /tmp/remote_balance_new; diff /tmp/remote_balance_old /tmp/remote_balance_new; cp /tmp/remote_balance_new /tmp/remote_balance_old; echo "$lines" | awk '{ print NR ": " '$n' - NR + 1  ": " $0 }' | column -t;  lncli listchannels  | grep '"active":' | sort | uniq -c | column -t;  echo; sleep 3m;  done
```


Close All Channels with no Remote Balance
=========================================

You may need to use this trick to be able to relay payments.

First, see the above section: ***Monitor Remote Balance in open Channels***

If there are no Remote Balances, that means no one has funds in channels open in your direction (even if you have funds in openned channels to others). In this case the root cause for me was that I did not set my external IP correctly. An easy way to get it right is like this:
```
lnd --externalip=$(dig +short myip.opendns.com @resolver1.opendns.com)
```
 
If external IP is set correctly, then the following can help maximize your chances of being a relay. With no Remote Balance there is nothing to relay.

Close all channels without remote balances:
```
    # try nicely, bilateral close
    lncli listchannels | grep '"remote_balance": "0"' -B 10   | awk -F'"' '/point/ {print $4}' | sort -R | while read cp; do           funding_txn=$(echo $cp | awk -F: '{print $1}');           output_index=$(echo $cp | awk -F: '{print $2}');           lncli closechannel   $funding_txn --output_index $output_index          ;         done

    # force all the ones that did not close bilaterally
    lncli listchannels | grep '"remote_balance": "0"' -B 10   | awk -F'"' '/point/ {print $4}' | sort -R | while read cp; do           funding_txn=$(echo $cp | awk -F: '{print $1}');           output_index=$(echo $cp | awk -F: '{print $2}');           lncli closechannel   $funding_txn --output_index $output_index  --force ;         done
```

Wait 1 or 2 days. Autopilot will establish new channels. Your peers may choose to commit balances to those channels which you'll see as `remote_balance`.

Here is a script to do all of the above every 24 hours:
```
while :; do                                        lncli listchannels | grep '"remote_balance": "0"' -B 10   | awk -F'"' '/point/ {print $4}' | sort -R | while read cp; do           funding_txn=$(echo $cp | awk -F: '{print $1}');           output_index=$(echo $cp | awk -F: '{print $2}');           lncli closechannel   $funding_txn --output_index $output_index ;  done;                                                                                                                                                                                                echo Graceful phase completed;   sleep 10;  lncli  listchannels | grep '"remote_balance": "0"' -B 10   | awk -F'"' '/point/ {print $4}' | sort -R | while read cp; do           funding_txn=$(echo $cp | awk -F: '{print $1}');           output_index=$(echo $cp | awk -F: '{print $2}');           lncli closechannel   $funding_txn --output_index $output_index --force ;          done;         echo Closed all channels without remote balances; date;  sleep 24h;   done
```

To do a backward incompatible upgrade of LND: Close All Channels
================================================================

This may be needed during backward incompatible upgrades of LND. Then you need to close all the channels before upgrading.

1. Restart LND with autopilot disabled.
2. Run
```
lncli listchannels | awk -F'"' '/point/ {print $4}' | while read cp; do 
  funding_txn=$(echo $cp | awk -F: '{print $1}');
  output_index=$(echo $cp | awk -F: '{print $2}'); 
  lncli closechannel $funding_txn --output_index $output_index; done
```
3. For uncooperative close, add **--force** to  `lncli closechannel` 

Pay Invoice Retry
=================

On testnet the graph is not well connected, so as Autopilot adds more channels to get connectivity, you may need to keep retying to pay an invoice. 

1. Side A: Create an invoice with longer expiry (default expiry is 1 hour, here 5867 is the requested amount in Satoshi):
```
lncli addinvoice --expiry $((3600 * 24)) 5867
```

2. Side B: Re-try until successful (get <pay_req> from step 1):
```
while :; do time lncli payinvoice <pay_req> || break; sleep 60; done
```

