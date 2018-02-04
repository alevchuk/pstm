# One-time Setup
```
# Requirement : become root, e.g. sudo su -l

apt-get install git

cd /
curl https://raw.githubusercontent.com/alevchuk/pstm/master/fs-time-machine/fs-gitignore > /.gitignore
curl https://raw.githubusercontent.com/alevchuk/pstm/master/fs-time-machine/fs-metadata-get.sh > /.fs-metadata-get.sh
chmod +x /.fs-metadata-get.sh

git init
```

# Example of making a commit for the whole file system
```
# Requirement : become root, e.g. sudo su -l

/.fs-metadata-get.sh && git add --all / && git commit -a -m 'LND Notes about SegWit addresses'
```


# What changed in directory X?
```
git status  # make another commit if necessary
git log --stat ~/.lnd
```

# What changed in file Y?
```
git log -p ~lightning/.lnd/lnd.conf
```

# What file permissions changed?
```
git log -p /.fs-metadata.acl-only
```
