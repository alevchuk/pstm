# System Requirements 
 
Read https://bitcoin.org/en/full-node#minimum-requirements
 
Yet, for me the disk usage does not seem to be as big as the above claims
 
1.2M    /home/lightning/.btcd/logs
16M /home/lightning/.lnd/logs
137M    /home/lightning/.lnd/data
15G /home/lightning/.btcd/data
15G total
 
 
# Security 
 
1. Setup firewall to _NO_ Incoming Connections before connecting to the network
 
  echo ":INPUT DROP [10636:1306803]
  :FORWARD DROP [0:0]
  :OUTPUT ACCEPT [649976:161157043]
  -A INPUT -i lo -j ACCEPT
  -A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
  -A OUTPUT -o lo -j ACCEPT" | iptables-restore
 
Persist firewall across reboots:
 
  apt-get install iptables-persistent
  copy rules to /etc/iptables/
 
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

3. Track changes to your filesystem:
 
  curl https://raw.githubusercontent.com/... > /.gitignore
  curl https://raw.githubusercontent.com/... > /.fs-metadata-get.sh
  chmod +x /.fs-metadata-get.sh
  /.fs-metadata-get.sh && git add --all / && git commit -a -m 'LND Notes about SegWit addresses'
 
4. Make unix account for lightning
  adduser lightning
 
 
# Backups 
 
Backup /.git to an external drive
 
  df -h
  mkdir /mnt/orig/
  mount /dev/sdb1 /mnt/orig/
  rsync -a --delete /.git/ /mnt/orig/home/backup/.git/
  umount /mnt/orig
 
 
# Ergonomics
 
Use your desktop account to sudo into root and lightning as needed
 
  screen
  sudo su  # screen tab for root
  sudo su -l lightning  # new tab
 
 
# Build Go
 
This is based on https://golang.org/doc/install/source
 
1. Fetch bootstrap go
 
  apt-get install golang-1.6
 
 
2. Set bootstrap path. To ~/.bashrc add:
 
  export GOOS=linux
  export GOARCH=amd64
  export GOROOT_BOOTSTRAP=/usr/lib/go-1.6
 
 
3. Fetch new go
 
  mkdir ~/src
  cd ~/src
  git clone https://go.googlesource.com/go
  cd go
  git fetch
  git checkout go1.9.2
 
4. Build new go
 
   . ~/.bashrc
   cd ~/src/go/src
   ./make.bash
 
 
# Build LND
 
This is based on https://github.com/lightningnetwork/lnd/blob/master/docs/INSTALL.md
 
1. Go Path, to ~/.bashrc add:
 
  export GOROOT=/home/lightning/src/go
  export GOPATH=$GOROOT
  export PATH=$GOPATH/bin:$PATH
 
2. Install Glide
 
   . ~/.bashrc
  old_gopath=$GOPATH && export GOPATH=~/gotmp1 && go get -u github.com/Masterminds/glide && mv ~/gotmp1/bin/glide $old_gopath/bin && echo Success! && rm -rf ~/gotmp1; export GOPATH=$old_gopath
 
 
3. Install LND and all dependencies (e.g. segwit capable btcd)
 
  git clone https://github.com/lightningnetwork/lnd $GOPATH/src/github.com/lightningnetwork/lnd
  cd $GOPATH/src/github.com/lightningnetwork/lnd
  glide install
  go install . ./cmd/...
 
4. Test
 
   go install; go test -v -p 1 $(go list ./... | grep -v  '/vendor/')
 
 
# Build BTCD
 
    git clone https://github.com/roasbeef/btcd $GOPATH/src/github.com/roasbeef/btcd
    cd $GOPATH/src/github.com/roasbeef/btcd
    glide install
    go install . ./cmd/...
 
 
# Start BTCD 
 
1. Place the following in ~/.lnd/lnd.conf
 
NOTE: generate some random values for rpcuser= and rpcpass=
 
 
    [Application Options]
   
    ; ------------------------------------------------------------------------------
    ; Data settings
    ; ------------------------------------------------------------------------------
   
    ; The directory to store data such as the block chain and peer addresses.  The
    ; block chain takes several GB, so this location must have a lot of free space.
    ; The default is ~/.btcd/data on POSIX OSes, $LOCALAPPDATA/Btcd/data on Windows,
    ; ~/Library/Application Support/Btcd/data on Mac OS, and $home/btcd/data on
    ; Plan9.  Environment variables are expanded so they may be used.  NOTE: Windows
    ; environment variables are typically %VARIABLE%, but they must be accessed with
    ; $VARIABLE here.  Also, ~ is expanded to $LOCALAPPDATA on Windows.
    ; datadir=~/.btcd/data
   
   
    ; ------------------------------------------------------------------------------
    ; Network settings
    ; ------------------------------------------------------------------------------
   
    ; Use testnet.
    testnet=1
   
    ; Connect via a SOCKS5 proxy.  NOTE: Specifying a proxy will disable listening
    ; for incoming connections unless listen addresses are provided via the 'listen'
    ; option.
    ; proxy=127.0.0.1:9050
    ; proxyuser=
    ; proxypass=
   
    ; The SOCKS5 proxy above is assumed to be Tor (https://www.torproject.org).
    ; If the proxy is not tor the following may be used to prevent using tor
    ; specific SOCKS queries to lookup addresses (this increases anonymity when tor
    ; is used by preventing your IP being leaked via DNS).
    ; noonion=1
   
    ; Use an alternative proxy to connect to .onion addresses. The proxy is assumed
    ; to be a Tor node. Non .onion addresses will be contacted with the main proxy
    ; or without a proxy if none is set.
    ; onion=127.0.0.1:9051
    ; onionuser=
    ; onionpass=
   
    ; Enable Tor stream isolation by randomizing proxy user credentials resulting in
    ; Tor creating a new circuit for each connection.  This makes it more difficult
    ; to correlate connections.
    ; torisolation=1
   
    ; Use Universal Plug and Play (UPnP) to automatically open the listen port
    ; and obtain the external IP address from supported devices.  NOTE: This option
    ; will have no effect if exernal IP addresses are specified.
    ; upnp=1
   
    ; Specify the external IP addresses your node is listening on.  One address per
    ; line.  btcd will not contact 3rd-party sites to obtain external ip addresses.
    ; This means if you are behind NAT, your node will not be able to advertise a
    ; reachable address unless you specify it here or enable the 'upnp' option (and
    ; have a supported device).
    ; externalip=1.2.3.4
    ; externalip=2002::1234
   
    ; ******************************************************************************
    ; Summary of 'addpeer' versus 'connect'.
    ;
    ; Only one of the following two options, 'addpeer' and 'connect', may be
    ; specified.  Both allow you to specify peers that you want to stay connected
    ; with, but the behavior is slightly different.  By default, btcd will query DNS
    ; to find peers to connect to, so unless you have a specific reason such as
    ; those described below, you probably won't need to modify anything here.
    ;
    ; 'addpeer' does not prevent connections to other peers discovered from
    ; the peers you are connected to and also lets the remote peers know you are
    ; available so they can notify other peers they can to connect to you.  This
    ; option might be useful if you are having problems finding a node for some
    ; reason (perhaps due to a firewall).
    ;
    ; 'connect', on the other hand, will ONLY connect to the specified peers and
    ; no others.  It also disables listening (unless you explicitly set listen
    ; addresses via the 'listen' option) and DNS seeding, so you will not be
    ; advertised as an available peer to the peers you connect to and won't accept
    ; connections from any other peers.  So, the 'connect' option effectively allows
    ; you to only connect to "trusted" peers.
    ; ******************************************************************************
   
    ; Add persistent peers to connect to as desired.  One peer per line.
    ; You may specify each IP address with or without a port.  The default port will
    ; be added automatically if one is not specified here.
    ; addpeer=192.168.1.1
    ; addpeer=10.0.0.2:8333
    ; addpeer=fe80::1
    ; addpeer=[fe80::2]:8333
   
    ; Add persistent peers that you ONLY want to connect to as desired.  One peer
    ; per line.  You may specify each IP address with or without a port.  The
    ; default port will be added automatically if one is not specified here.
    ; NOTE: Specifying this option has other side effects as described above in
    ; the 'addpeer' versus 'connect' summary section.
    ; connect=192.168.1.1
    ; connect=10.0.0.2:8333
    ; connect=fe80::1
    ; connect=[fe80::2]:8333
   
    ; Maximum number of inbound and outbound peers.
    ; maxpeers=125
   
    ; Disable banning of misbehaving peers.
    ; nobanning=1
   
    ; Maximum allowed ban score before disconnecting and banning misbehaving peers.`
    ; banthreshold=100
   
    ; How long to ban misbehaving peers. Valid time units are {s, m, h}.
    ; Minimum 1s.
    ; banduration=24h
    ; banduration=11h30m15s
   
    ; Add whitelisted IP networks and IPs. Connected peers whose IP matches a
    ; whitelist will not have their ban score increased.
    ; whitelist=127.0.0.1
    ; whitelist=::1
    ; whitelist=192.168.0.0/24
    ; whitelist=fd00::/16
   
    ; Disable DNS seeding for peers.  By default, when btcd starts, it will use
    ; DNS to query for available peers to connect with.
    ; nodnsseed=1
   
    ; Specify the interfaces to listen on.  One listen address per line.
    ; NOTE: The default port is modified by some options such as 'testnet', so it is
    ; recommended to not specify a port and allow a proper default to be chosen
    ; unless you have a specific reason to do otherwise.
    ; All interfaces on default port (this is the default):
    ;  listen=
    ; All ipv4 interfaces on default port:
    ;  listen=0.0.0.0
    ; All ipv6 interfaces on default port:
    ;   listen=::
    ; All interfaces on port 8333:
    ;   listen=:8333
    ; All ipv4 interfaces on port 8333:
    ;   listen=0.0.0.0:8333
    ; All ipv6 interfaces on port 8333:
    ;   listen=[::]:8333
    ; Only ipv4 localhost on port 8333:
    listen=127.0.0.1:18335
   
    ; Only ipv6 localhost on port 8333:
    ;   listen=[::1]:8333
    ; Only ipv4 localhost on non-standard port 8336:
    ;   listen=127.0.0.1:8336
    ; All interfaces on non-standard port 8336:
    ;   listen=:8336
    ; All ipv4 interfaces on non-standard port 8336:
    ;   listen=0.0.0.0:8336
    ; All ipv6 interfaces on non-standard port 8336:
    ;   listen=[::]:8336
   
    ; Disable listening for incoming connections.  This will override all listeners.
    ; nolisten=1
   
    ; Disable peer bloom filtering.  See BIP0111.
    ; nopeerbloomfilters=1
   
    ; Add additional checkpoints. Format: '<height>:<hash>'
    ; addcheckpoint=<height>:<hash>
   
    ; Add comments to the user agent that is advertised to peers.
    ; Must not include characters '/', ':', '(' and ')'.
    ; uacomment=
   
    ; Disable committed peer filtering (CF).
    ; nocfilters=1
   
    ; ------------------------------------------------------------------------------
    ; RPC server options - The following options control the built-in RPC server
    ; which is used to control and query information from a running btcd process.
    ;
    ; NOTE: The RPC server is disabled by default if rpcuser AND rpcpass, or
    ; rpclimituser AND rpclimitpass, are not specified.
    ; ------------------------------------------------------------------------------
   
    ; Secure the RPC API by specifying the username and password.  You can also
    ; specify a limited username and password.  You must specify at least one
    ; full set of credentials - limited or admin - or the RPC server will
    ; be disabled.
    rpcuser=
    rpcpass=
 
    ; rpclimituser=whatever_limited_username_you_want
    ; rpclimitpass=
   
    ; Specify the interfaces for the RPC server listen on.  One listen address per
    ; line.  NOTE: The default port is modified by some options such as 'testnet',
    ; so it is recommended to not specify a port and allow a proper default to be
    ; chosen unless you have a specific reason to do otherwise.  By default, the
    ; RPC server will only listen on localhost for IPv4 and IPv6.
    ; All interfaces on default port:
    ;   rpclisten=
    ; All ipv4 interfaces on default port:
    ;   rpclisten=0.0.0.0
    ; All ipv6 interfaces on default port:
    ;   rpclisten=::
    ; All interfaces on port 8334:
    ;   rpclisten=:8334
    ; All ipv4 interfaces on port 8334:
    ;   rpclisten=0.0.0.0:8334
    ; All ipv6 interfaces on port 8334:
    ;   rpclisten=[::]:8334
    ; Only ipv4 localhost on port 8334:
    ;   rpclisten=127.0.0.1:8334
    ; Only ipv6 localhost on port 8334:
    ;   rpclisten=[::1]:8334
    ; Only ipv4 localhost on non-standard port 8337:
    ;   rpclisten=127.0.0.1:8337
    ; All interfaces on non-standard port 8337:
    ;   rpclisten=:8337
    ; All ipv4 interfaces on non-standard port 8337:
    ;   rpclisten=0.0.0.0:8337
    ; All ipv6 interfaces on non-standard port 8337:
    ;   rpclisten=[::]:8337
   
    ; Specify the maximum number of concurrent RPC clients for standard connections.
    ; rpcmaxclients=10
   
    ; Specify the maximum number of concurrent RPC websocket clients.
    ; rpcmaxwebsockets=25
   
    ; Mirror some JSON-RPC quirks of Bitcoin Core -- NOTE: Discouraged unless
    ; interoperability issues need to be worked around
    ; rpcquirks=1
   
    ; Use the following setting to disable the RPC server even if the rpcuser and
    ; rpcpass are specified above.  This allows one to quickly disable the RPC
    ; server without having to remove credentials from the config file.
    ; norpc=1
   
    ; Use the following setting to disable TLS for the RPC server.  NOTE: This
    ; option only works if the RPC server is bound to localhost interfaces (which is
    ; the default).
    ; notls=1
   
   
    ; ------------------------------------------------------------------------------
    ; Mempool Settings - The following options
    ; ------------------------------------------------------------------------------
   
    ; Set the minimum transaction fee to be considered a non-zero fee,
    ; minrelaytxfee=0.00001
   
    ; Rate-limit free transactions to the value 15 * 1000 bytes per
    ; minute.
    ; limitfreerelay=15
   
    ; Require high priority for relaying free or low-fee transactions.
    ; norelaypriority=0
   
    ; Limit orphan transaction pool to 100 transactions.
    ; maxorphantx=100
   
    ; Do not accept transactions from remote peers.
    ; blocksonly=1
   
    ; Relay non-standard transactions regardless of default network settings.
    ; relaynonstd=1
   
    ; Reject non-standard transactions regardless of default network settings.
    ; rejectnonstd=1
   
   
    ; ------------------------------------------------------------------------------
    ; Optional Transaction Indexes
    ; ------------------------------------------------------------------------------
   
    ; Build and maintain a full address-based transaction index.
    ; addrindex=1
    ; Delete the entire address index on start up, then exit.
    ; dropaddrindex=0
   
   
    ; ------------------------------------------------------------------------------
    ; Optional Indexes
    ; ------------------------------------------------------------------------------
   
    ; Build and maintain a full hash-based transaction index which makes all
    ; transactions available via the getrawtransaction RPC.
    txindex=1
   
    ; Build and maintain a full address-based transaction index which makes the
    ; searchrawtransactions RPC available.
    ; addrindex=1
   
   
    ; ------------------------------------------------------------------------------
    ; Signature Verification Cache
    ; ------------------------------------------------------------------------------
   
    ; Limit the signature cache to a max of 50000 entries.
    ; sigcachemaxsize=50000
   
   
    ; ------------------------------------------------------------------------------
    ; Coin Generation (Mining) Settings - The following options control the
    ; generation of block templates used by external mining applications through RPC
    ; calls as well as the built-in CPU miner (if enabled).
    ; ------------------------------------------------------------------------------
   
    ; Enable built-in CPU mining.
    ;
    ; NOTE: This is typically only useful for testing purposes such as testnet or
    ; simnet since the difficutly on mainnet is far too high for CPU mining to be
    ; worth your while.
    ; generate=false
   
    ; Add addresses to pay mined blocks to for CPU mining and potentially in the
    ; block templates generated for the getblocktemplate RPC.  One address per line.
    ; miningaddr=1yourbitcoinaddress
    ; miningaddr=1yourbitcoinaddress2
    ; miningaddr=1yourbitcoinaddress3
   
    ; Specify the minimum block size in bytes to create.  By default, only
    ; transactions which have enough fees or a high enough priority will be included
    ; in generated block templates.  Specifying a minimum block size will instead
    ; attempt to fill generated block templates up with transactions until it is at
    ; least the specified number of bytes.
    ; blockminsize=0
   
    ; Specify the maximum block size in bytes to create.  This value will be limited
    ; to the consensus limit if it is larger than that value.
    ; blockmaxsize=750000
   
    ; Specify the size in bytes of the high-priority/low-fee area when creating a
    ; block.  Transactions which consist of large amounts, old inputs, and small
    ; sizes have the highest priority.  One consequence of this is that as low-fee
    ; or free transactions age, they raise in priority thereby making them more
    ; likely to be included in this section of a new block.  This value is limited
    ; by the blackmaxsize option and will be limited as needed.
    ; blockprioritysize=50000
   
   
    ; ------------------------------------------------------------------------------
    ; Debug
    ; ------------------------------------------------------------------------------
   
    ; Debug logging level.
    ; Valid levels are {trace, debug, info, warn, error, critical}
    ; You may also specify <subsystem>=<level>,<subsystem2>=<level>,... to set
    ; log level for individual subsystems.  Use btcd --debuglevel=show to list
    ; available subsystems.
    ; debuglevel=info
   
    ; The port used to listen for HTTP profile requests.  The profile server will
    ; be disabled if this option is not specified.  The profile information can be
    ; accessed at http://localhost:<profileport>/debug/pprof once running.
    ; profile=6061
 
 
2. Run:

```
btcd

# It will take several days to replicate and verify the blockchain:
# Laptop (Taurinus, 3.9G RAM):            4 days
# Amazon AWS (t2.micro, 0.9G RAM):        4 days
# Google VM (Intel N1, 1 VCPU, 3.7G RAM): 1 day
```
 
# Start LND
 
    1. Place the following in ~/.lnd/lnd.conf
   
    [Application Options]
   
    ; The directory that lnd stores all wallet, chain, and channel related data
    ; within The default is ~/.lnd/data on POSIX OSes, $LOCALAPPDATA/Lnd/data on
    ; Windows, ~/Library/Application Support/Lnd/data on Mac OS, and $home/lnd/data
    ; on Plan9.  Environment variables are expanded so they may be used.  NOTE:
    ; Windows environment variables are typically %VARIABLE%, but they must be
    ; accessed with $VARIABLE here.  Also, ~ is expanded to $LOCALAPPDATA on Windows.
    ; datadir=~/.lnd/data
   
    ; The directory that logs are stored in. The logs are auto-rotated by default.
    ; Rotated logs are compressed in place.
    ; logdir=~/.lnd/logs
   
    ; Path to TLS certificate for lnd's RPC and REST services.
    ; tlscertpath=~/.lnd/tls.cert
   
    ; Path to TLS private key for lnd's RPC and REST services.
    ; tlskeypath=~/.lnd/tls.key
   
    ; Disable macaroon authentication. Macaroons are used are bearer credentials to
    ; authenticate all RPC access. If one wishes to opt out of macaroons, uncomment
    ; the line below.
    ; no-macaroons=true
   
    ; Path to write the admin macaroon for lnd's RPC and REST services if it
    ; doesn't exist. This can be set if one wishes to store the admin macaroon in a
    ; distinct location. By default, it is stored within lnd's main home directory.
    ; Applications that are able to read this file, gains admin macaroon access
    ; adminmacaroonpath=~/.lnd/admin.macaroon
   
    ; Path to write the read-only macaroon for lnd's RPC and REST services if it
    ; doesn't exist. This can be set if one wishes to store the read-only macaroon
    ; in a distinct location. The read only macaroon allows users which can read
    ; the file to access RPC's which don't modify the state of the daemon.
    ; readonlymacaroonpath=~/.lnd/readonly.macaroon
                           
   
    ; Specify the interfaces to listen on.  One listen address per line.
    ; All interfaces on default port (this is the default):
    ;  listen=
    ; Only ipv4 localhost on port 999:
    ;   listen=127.0.0.1:999
   
   
    ; Adding an external IP will advertise your node to the network. This signals
    ; that your node is available to accept incoming channels. If you don't wish to
    ; advertise your node, this value doesn't need to be set.
    ;externalip=            
   
   
    ; Debug logging level.
    ; Valid levels are {trace, debug, info, warn, error, critical}
    ; You may also specify <subsystem>=<level>,<subsystem2>=<level>,... to set
    ; log level for individual subsystems.  Use btcd --debuglevel=show to list
    ; available subsystems.
    ; debuglevel=info
   
    ; Write CPU profile to the specified file.
    ;cpuprofile=
   
    ; Enable HTTP profiling on given port -- NOTE port must be between 1024 and
    ; 65536. The profile can be access at: http://localhost:<PORT>/debug/pprof/.
    ;profile=
   
    ; The port to listen on for incoming p2p connections. The default port is 9735.
    ; peerport=9735
   
    ; The port that the gRPC server will listen on.
    ; rpcport=10009
   
    ; The port that the HTTP REST proxy to the gRPC server will listen on.
    ; restport=8080
   
    ; The maximum number of incoming pending channels permitted per peer.
    ; maxpendingchannels=1
   
    ; The default number of confirmations a channel must have before it's considered
    ; open. We'll require any incoming channel requests to wait this many
    ; confirmations before we consider the channel active.
    ; defaultchanconfs=3
                           
    ; If true, then automatic network bootstrapping will not be attempted. This
    ; means that your node won't attempt to automatically seek out peers on the
    ; network.
    ; nobootstrap=1
   
    ; If set, your wallet will be encrypted with the default passphrase. This isn't
    ; recommend, as if an attacker gains access to your wallet file, they'll be able
    ; to decrypt it. This value is ONLY to be used in testing environments.
    ; noencryptwallet=1
   
   
    [Bitcoin]
   
    ; If the Bitcoin chain should be active. Atm, only a single chain can be
    ; active.
    bitcoin.active=1
   
    ; The host that your local btcd daemon is listening on. This MUST be set if
    ; neutrino mode isn't active.
    ; bitcoin.rpchost=localhost
                 
    ; Username for RPC connections to btcd. This only needs to be set if neutrino
    ; mode isn't active. By default, lnd will attempt to automatically obtain the
    ; credentials, so this likely won't need to be set (other than for simnet mode).
    ; bitcoin.rpcuser=kek
   
    ; Password for RPC connections to btcd. This only needs to be set if neutrino
    ; mode isn't active. By default, lnd will attempt to automatically obtain the
    ; credentials, so this likely won't need to be set (other than for simnet mode).
    ; bitcoin.rpcpass=kek
   
    ; File containing the daemon's certificate file. This only needs to be set if
    ; the node isn't on the same host as lnd.
    ; bitcoin.rpccert=~/.btcd/rpc.cert
   
    ; The raw bytes of the daemon's PEM-encoded certificate chain which will be used
    ; to authenticate the RPC connection. This only needs to be set if the btcd
    ; node is on a remote host.
    ; bitcoin.rawrpccert=  
   
    ; Use Bitcoin's test network.
    bitcoin.testnet=1
    ;
    ; Use Bitcoin's simulation test network
    ; bitcoin.simnet=0
   
    ; Use Bitcoin's regression test network
    ; bitcoin.regtest=false
   
   
    [Litecoin]
   
    ; If the Litecoin chain should be active. Atm, only a single chain can be
    ; active.
    ; litecoin.active=1
   
    ; The host that your local ltcd daemon is listening on. This MUST be set if
    ; neutrino mode isn't active.
    ; litecoin.rpchost=localhost
                 
    ; Username for RPC connections to ltcd. This only needs to be set if neutrino
    ; mode isn't active.
    ; litecoin.rpcuser=
   
    ; Password for RPC connections to ltcd. This only needs to be set if neutrino
    ; mode isn't active.
    ; litecoin.rpcpass=
   
    ; File containing the daemon's certificate file. This only needs to be set if
    ; the node isn't on the same host as lnd.
    ; litecoin.rpccert=~/.btcd/rpc.cert
   
    ; The raw bytes of the daemon's PEM-encoded certificate chain which will be used
    ; to authenticate the RPC connection. This only needs to be set if the ltcd
    ; node is on a remote host.
    ; litecoin.rawrpccert=  
   
    ; Use Bitcoin's test network.
    ; litecoin.testnet=1
    ;
    ; Use Bitcoin's simulation test network
    ; litecoin.simnet=0
   
    ; Use Bitcoin's regression test network
    ; litecoin.regtest=false
   
   
    [neutrino]
   
    ; If the light client mode should be active or not. This mode requires less
    ; disk space as it doesn't require one to have full-node locally. Instead,
    ; neutrino will connect to the P2P network for all of lnd's needs.
    neutrino.active=false
   
    ; Connect only to the specified peers at startup. This creates a persistent
    ; connection to a target peer. This is recommend as there aren't many neutrino
    ; compliant full nodes on the test network yet.
    ;neutrino.connect=
   
    ; Add a peer to connect with at startup.
    ;neutrino.addpeer=
   
    [autopilot]
   
    ; If the autopilot agent should be active or not. The autopilot agent will
    ; attempt to automatically open up channels to put your node in an advantageous
    ; position within the network graph.
    ; autopilot.active=1
   
    ; The maximum number of channels that should be created.
    ; autopilot.maxchannels=5
   
    ; The percentage of total funds that should be committed to automatic channel
    ; establishment
    ; autopilot.allocation=0.6
 
2. Bash completion for lncli
 
```
cp /home/lightning/src/go/src/github.com/lightningnetwork/lnd/contrib/lncli.bash-completion /etc/bash_completion.d/lncli
# in Debian install "bash-completion" and uncomment "enable bash completion" in /etc/bash.bashrc
```

3. Run
 
 ```
 lnd
 ```
 
4. Create a wallet
 
```
lncli create
```

5. Get some free testing bitcoin
 
 ```
lncli newaddress np2wkh  # Nested SegWit address
```

Paste the address into https://testnet.coinfaucet.eu/en/, get txn link, wait for 6 confirmations.

```
lncli walletbalance  # will show unconfirmed balance within a few seconds, and confirmed in 2 hours
```
 
6. Enable autopilot by commenting out the last 3 properties in lnd.conf, then check activity in 1 hour:
 
```
lncli walletbalance
lncli channelbalance
lncli listchannels  | grep active | sort | uniq -c  # number of open channels
lncli listpeers | grep inbound | uniq -c  # to be a relay you'll need to get inbound peers
```
 
7. Keep track of your balance:
 
Use [get_balance_report.py script](get_balance_report.py)
```
curl https://raw.githubusercontent.com/alevchuk/pstm/master/lnd-e2e-testing/get_balance_report.py > ~/get_balance_report.py
chmod +x ~/get_balance_report.py
~/get_balance_report.py
```

8. To get incomming channels you'll need allow incomming connections on port 9735
 
open port in iptabels rules (don't froget to persit in /etc/...)

      iptables -I INPUT -p tcp --dport 9735 -j ACCEPT
   
configures your home router to do port forwarding
   
start LND with your external IP specified:
   
```
lnd --externalip=$(dig +short myip.opendns.com @resolver1.opendns.com)
```

test with netcat from a differet host
   
```
echo hi | nc <external_ip_of_LND_host> 9735
```

lnc logs will show

      2018-01-08 20:41:07.856 [ERR] CMGR: Can't accept connection: unexpected EOF