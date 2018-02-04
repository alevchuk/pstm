# One-time Setup
```
apt-get install git

cd /
curl https://raw.githubusercontent.com/alevchuk/pstm/master/fs-time-machine/fs-gitignore > /.gitignore
curl https://raw.githubusercontent.com/alevchuk/pstm/master/fs-time-machine/fs-metadata-get.sh > /.fs-metadata-get.sh
chmod +x /.fs-metadata-get.sh

git init
```

# Example of making a commit for the whole file system
```
/.fs-metadata-get.sh && git add --all / && git commit -a -m 'LND Notes about SegWit addresses'
```
