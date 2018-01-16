Monitor number of Active Channels
=================================
```
while :; do 
  echo "$(date) $(lncli listchannels  | grep '"active": true,' | sort | uniq -c)"; sleep 60; done
```

Close All Channels
==================

1. Restart LND with autopilot disabled.
2. Run
```
lncli listchannels | grep '"active": true' -A 2 | awk -F'"' '/point/ {print $4}' | while read cp; do 
  funding_txn=$(echo $cp | awk -F: '{print $1}');
  output_index=$(echo $cp | awk -F: '{print $2}'); 
  lncli closechannel $funding_txn --output_index $output_index; done
```
3. For uncooperative close, add **-f** to  `lncli closechannel` 

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

