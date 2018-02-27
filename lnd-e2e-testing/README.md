This is a step-by-step technical guide on how to setup [LND](https://github.com/lightningnetwork/lnd) with Autopilot in Bitcoin Testnet. Security and Backup sections are a consideration for the future - they can be skipped because Testnet does not involve real funds.

Table of contents
=================

  * [System Requirements](#system-requirements)
  * [Security](#security)
  * [Backups](#backups)
  * [Ergonomics](#ergonomics)
  * [Build Go](#build-go)
  * [Build LND](#build-lnd)
  * [Build BTCD](#build-btcd)
  * [Configure BTCD](#configure-btcd)
  * [Start BTCD - this step takes 1 to 4 days](#start-btcd)
  * [Configure LND](#configure-lnd)
  * [Start LND](#start-lnd)
  * [Fund your LND wallet and enable AutoPilot](#fund-your-lnd-wallet-and-enable-autopilot)
  * [Enable incoming channels](#enable-incoming-channels)
  
# System Requirements 
 
Read https://bitcoin.org/en/full-node#minimum-requirements for Bitcoin blockchain requirements.

You need 4 GB of RAM because LND can get memory hungry at times. Yet currently my LND process runs with 1.3 GB virtual memory (of which 600 MB is in RSS).
 
For testnet the disk usage will be 8x smaller than the 145 GB mainnet recommendation:

    du -sch ~/*
    ...
    1.2M  /home/lightning/.btcd/logs
    16M   /home/lightning/.lnd/logs
    ...
    2.G   /home/lightning/.lnd/data
    15G   /home/lightning/.btcd/data
    
    18G total

 
# Security 
 
0. Use hardware that you control (e.g. laptop) and trust. E.g. I don't trust Intel's proprietary firmare because of the [known flaws in their remote administration features](https://www.wired.com/story/intel-management-engine-vulnerabilities-pcs-servers-iot/). A good start would be hardware that is certified by Free Software Foundation: https://www.fsf.org/resources/hw/endorsement/respects-your-freedom because the firmware is open source and can be audited.

1. When setting up your laptop, make firewall _Drop all_ Incoming Connections _before_ connecting to the network. Later you may need to open 1 port for Lightning (see [Enable incoming channels](#enable-incoming-channels))

```
echo ":INPUT DROP
:FORWARD DROP
:OUTPUT ACCEPT
-A INPUT -i lo -j ACCEPT
-A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A OUTPUT -o lo -j ACCEPT" | iptables-restore
```

Persist firewall across reboots:

    apt-get install iptables-persistent
    iptables-save  # show current rules
    # Copy rules to /etc/iptables/
    # Reboot to test persistence
 
2. Run system updates regularly
 
```
apt-get install aptitude
sudo aptitude
# press "/" to search for packages
# press "+" to select a package for installing
# press "-" to de-select
# press Enter to read more able the package, "q" to go back
# press "u" to refresh cache
# press "U" to select all available upgrades
# press "g" to review changes before installing
# press "g" again to install/upgrade
```

3. Track changes to your filesystem. This can come in handy when you get paranoid (e.g. what changed after laptop update or reboot?)

E.g. you can use [alevchuk/pstm/fs-time-machine method](../fs-time-machine) of tracking fs changes:
```
cd /
curl https://raw.githubusercontent.com/alevchuk/pstm/master/fs-time-machine/fs-gitignore > /.gitignore
curl https://raw.githubusercontent.com/alevchuk/pstm/master/fs-time-machine/fs-metadata-get.sh > /.fs-metadata-get.sh
chmod +x /.fs-metadata-get.sh
git init

/.fs-metadata-get.sh && git add --all / && git commit -a -m 'LND Notes about SegWit addresses'
```

4. Make unix account for lightning
```
adduser lightning
``` 
 
# Backups 
 
Backup /.git to an external drive
 
    df -h
    mkdir /mnt/orig/
    mount /dev/sdb1 /mnt/orig/
    rsync -a --delete /.git/ /mnt/orig/home/backup/.git/
    umount /mnt/orig
 
 
# Ergonomics
 
Configure ~/.screenrc so it lables tabs, has good scrollback history, and always shows what host your on, e.g. Laptop, AWS, Google Cloud, ... (I setup addtition nodes in the clouds for temorary experiments. Yet, the dedicated laptop node is the only one I'd trust)

    escape ^Bb
    defscrollback 60000
    maptimeout 0
    defhstatus 'amazon'
    hardstatus alwayslastline '%{= G}[ %{G} %h %{g} ][%= %{= w}%?%-Lw%?%{= B}%n*%f %t%?%{= B}(%u)%?%{= w}%+Lw%?%= %{= g}][%{B} %Y %{g}]'

Use your "desktop" account to sudo into root and lightning as needed
 
    screen
    
    sudo su  # screen tab for root
    sudo su -l lightning  # new tab
 
 
# Build Go
 
This is based on https://golang.org/doc/install/source
 
1. Fetch bootstrap go
 
```
apt-get install golang-1.6
```
 
2. Set bootstrap path. To ~/.bashrc add:

```
export GOOS=linux
export GOARCH=amd64
export GOROOT_BOOTSTRAP=/usr/lib/go-1.6
```
 
3. Fetch new go
```
mkdir ~/src
cd ~/src
git clone https://go.googlesource.com/go
cd go
git fetch
git checkout go1.9.2
```

4. Build new go
```
. ~/.bashrc
cd ~/src/go/src
./make.bash
```
 
# Build LND
 
This is based on https://github.com/lightningnetwork/lnd/blob/master/docs/INSTALL.md
 
1. Go Path, to ~/.bashrc add:
```
export GOROOT=/home/lightning/src/go
export GOPATH=$GOROOT
export PATH=$GOPATH/bin:$PATH
```

2. Install Glide
```
. ~/.bashrc

old_gopath=$GOPATH && export GOPATH=~/gotmp1 && go get -u github.com/Masterminds/glide && mv ~/gotmp1/bin/glide $old_gopath/bin && echo Success! && rm -rf ~/gotmp1; export GOPATH=$old_gopath
```
 
3. Install LND and all dependencies (e.g. segwit capable btcd)
```
git clone https://github.com/lightningnetwork/lnd $GOPATH/src/github.com/lightningnetwork/lnd
cd $GOPATH/src/github.com/lightningnetwork/lnd
glide install
go install . ./cmd/...
```

4. Test
```
go install; go test -v -p 1 $(go list ./... | grep -v  '/vendor/')
```
 
# Build BTCD
 
    git clone https://github.com/roasbeef/btcd $GOPATH/src/github.com/roasbeef/btcd
    cd $GOPATH/src/github.com/roasbeef/btcd
    glide install
    go install . ./cmd/...
 
 
# Configure BTCD 
 
1. Copy the official config sample https://github.com/Roasbeef/btcd/blob/master/sample-btcd.conf
   ```
   curl https://raw.githubusercontent.com/Roasbeef/btcd/master/sample-btcd.conf > ~/.btcd/sample-btcd.conf 
   ```
    
2. Find, uncomment (remove ";") and set the following config option
   ```
   testnet=1
   rpcuser=
   rpcpass=
   ```
3. Generate some random values for `rpcuser=` and `rpcpass=`
 
4. Place the config:
   ```
   diff ~/.btcd/sample-btcd.conf ~/.btcd/btcd.conf
   cp   ~/.btcd/sample-btcd.conf ~/.btcd/btcd.conf
   ```
 
 
# Start BTCD 

Run:

```
btcd

# It will take several days to replicate and verify the blockchain:
# Laptop (Taurinus, 3.9G RAM):            4 days
# Amazon AWS (t2.micro, 0.9G RAM):        4 days
# Google VM (Intel N1, 1 VCPU, 3.7G RAM): 1 day
```
 
# Configure LND
 
   1. Copy the official config sample https://github.com/lightningnetwork/lnd/blob/master/sample-lnd.conf 
   ```
   curl https://raw.githubusercontent.com/lightningnetwork/lnd/master/sample-lnd.conf > ~/.lnd/sample-lnd.conf 
   ```
    
   2. Find and change the following config options in ~/.lnd/sample-lnd.conf 
   ```
   debuglevel=ATPL=debug,CRTR=warn
   bitcoin.simnet=0
   bitcoin.testnet=1
    
   autopilot.active=1
   autopilot.maxchannels=20
   autopilot.allocation=1.0
   ```
   
   3. Place the config
   ```
   diff ~/.lnd/sample-lnd.conf ~/.lnd/lnd.conf
   cp   ~/.lnd/sample-lnd.conf ~/.lnd/lnd.conf
   ```
 
# Start LND
1. Bash completion for lncli, which was contributed to LND by [Andreas M. Antonopoulos](https://github.com/lightningnetwork/lnd/commits/master/contrib/lncli.bash-completion)
 
```
cp /home/lightning/src/go/src/github.com/lightningnetwork/lnd/contrib/lncli.bash-completion /etc/bash_completion.d/lncli
# in Debian install "bash-completion" and uncomment "enable bash completion" in /etc/bash.bashrc
```

2. Run
 
 ```
 lnd
 ```
 
3. Create a wallet
 
```
lncli create
```

# Fund your LND wallet and enable AutoPilot

1. Get some free testing bitcoin
 
 ```
lncli newaddress np2wkh  # Nested SegWit address
```

Paste the address into https://testnet.coinfaucet.eu/en/, get txn link, wait for 6 confirmations.

```
lncli walletbalance  # will show unconfirmed balance within a few seconds, and confirmed in 2 hours
```
 
2. Enable autopilot by commenting out the last 3 properties in lnd.conf
3. Restart LND
4. Then check activity in 1 hour:
 
```
lncli walletbalance
lncli channelbalance
lncli listchannels  | grep active | sort | uniq -c  # number of open channels
lncli listpeers | grep inbound | uniq -c  # to be a relay you'll need to get inbound peers
```
 
5. Keep track of your total balance:
 
Use [get_balance_report.py script](get_balance_report.py)
```
curl https://raw.githubusercontent.com/alevchuk/pstm/master/lnd-e2e-testing/get_balance_report.py > ~/get_balance_report.py
chmod +x ~/get_balance_report.py
~/get_balance_report.py
```

As channels open and close you may see total balance go down but should it recover eventually.

# Enable incoming channels

To get incoming channels you'll need allow incoming connections on port 9735:
 
1. Open port in iptabels rules (don't froget to persit in /etc/...)

```
iptables -I INPUT -p tcp --dport 9735 -j ACCEPT
```

2. Configure your home router to do port forwarding
   
3. Start LND with your external IP specified:
   
```
lnd --externalip=$(dig +short myip.opendns.com @resolver1.opendns.com)

# On Debian, to get dig, you'll need to install the "dnsutils" package
```

4. Test with netcat from a different host
   
```
echo hi | nc <external_ip_of_LND_host> 9735
```

lnc logs will show

      2018-01-08 20:41:07.856 [ERR] CMGR: Can't accept connection: unexpected EOF
