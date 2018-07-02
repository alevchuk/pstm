# Setting up Lightning Network Explorer

## 1. Install dependencies

Node needs bzip2 and C++ compiler that's new enough: g++ 4.9.4 or clang++ 3.4.2 

    sudo apt-get install clang bzip2
    
## 2. Create new account
    sudo adduser lightning
    sudo su -l recksplorer

## 3. Install Node
    wget https://nodejs.org/dist/v8.11.3/node-v8.11.3.tar.gz
    tar zxvf node-v8.11.3.tar.gz
    cd ~/node-v8.11.3
    CXX=clang++ ./configure --prefix=~/node
    make
    make install

    echo 'export PATH=~/node/bin:$PATH' >> ~/.bashrc
    . ~/.bashrc
    
## 4. Install recksplorer

    git clone https://github.com/chemicstry/recksplorer.git
    cd recksplorer
    npm install 

I get 3 warnings that looks like this https://gist.github.com/alevchuk/01163b6ee12738bb8e408ff146b19aeb, it's Ok
    
    npm rebuild grpc
    
## 5. Copy LND RPC access credentials

From admin account run

    sudo mkdir ~recksplorer/.lnd
    sudo cp ~lightning/.lnd/tls.cert ~recksplorer/.lnd/
    sudo cp ~lightning/.lnd/admin.macaroon ~recksplorer/.lnd/
    sudo chown -R recksplorer ~recksplorer/.lnd
    
## 6. Start recksplorer

    cd ~/recksplorer
    node ./server -p 1234

