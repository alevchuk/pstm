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

Safe default config for AutoPilot is:

```
autopilot.active=1
autopilot.maxchannels=5
autopilot.allocation=1.0
```

The reason you should initially set maxchannels to not more than 5 is descirbed in https://github.com/lightningnetwork/lnd/issues/772 It is a bug in LND.

With larger maxchannels you will end out running out of number of open files. On some Linux distributions it will take longer on others it will happend sooner depending on the default **Max open files** settings.

Check the current limits:
```
cat /proc/$(pgrep lnd)/limits  | grep files
Max open files            1024                 1048576              files
```
The first number 1024 is the soft limit that will cause LND to crash if it opens that many "files" (actually Netwrok connections).

Workaround:

1. Increase the soft limit to ~500k by adding:
```
*                soft    nofile          524288
*                hard    nofile          1048576
```
to `/etc/security/limits.conf`
2. Check `dmesg` for errors relating to limits.conf syntax
3. Stop LND and log-out/exit of the bash shell 
4. Start a new shell session (e.g. open a new Screen/Tmux window)
5. Star LND
6. Check that new limits are set: `cat /proc/$(pgrep lnd)/limits  | grep files`

Now, you can increase `autopilot.maxchannels`  in `~/.lnd/lnd.conf` and restart LND again
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

Wait 48 hours. Autopilot will establish new channels. Your peers may choose to commit balances to those channels which you'll see as `remote_balance`.


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

