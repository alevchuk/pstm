Close All Channels
==================

1. Restart LND with autopilot disabled.
2. Run
```
lncli listchannels | grep '"active": true' -A 2 | grep point |  awk -F'"' '{print $4}' | while read cp; do funding_txn=$(echo $cp | awk -F: '{print $1}'); oi=$(echo $cp | awk -F: '{print $2}'); lncli closechannel $funding_txn --output_index $oi; done
```
3. For uncooperative close, add **-f** to  `lncli closechannel` 
