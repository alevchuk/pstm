#!/bin/bash

# Persist metadata changes of your file system, indended to use with source control of your /
# Before using this do:
# curl https://raw.githubusercontent.com/alevchuk/pstm/master/fs-gitignore > /.gitignore
# cd /
# git init
# time git add .  # this may take a while
# git commit -a -m 'first commit'

set -u
set -e

cd /
result_file=".fs-metadata"
result_acl_file=".fs-metadata.acl-only"
result_timestamp_file=".fs-metadata.timestamp-only"
result_data_file=".fs-metadata.data-only"
tmp_metadata=".fs-metadata.tmp"
tmp_deleted=".fs-metadata-deleted-files.tmp"

# Find which files were deleted files
git status -s | awk '$1=="D" {print $2}' > $tmp_deleted

#
# Stat all files
#
get_metadata() {
  #  1 %n     file name
  #  2 %s     total size, in bytes
  #  3 %b     number of blocks allocated (see %B)
  #  4 %f  A  raw mode in hex
  #  5 %u  A  user ID of owner
  #  6 %g  A  group ID of owner
  #  7 %D     device number in hex
  #  8 %i     inode number
  #  9 %h     number of hard links
  # 10 %t     major device type in hex
  # 11 %T     minor device type in hex
  # 12 %X  T  time of last access, seconds since Epoch
  # 13 %Y  T  time of last modification, seconds since Epoch
  # 14 %Z  T  time of last meta data changed (e.g. permissions)
  # 15 %W  T  time of file birth, seconds since Epoch; 0 if unknown
  # 16 %o     optimal I/O transfer size hint

  set +u
  xargs $1 stat -c "%n %s %b %f %u %g %D %i %h %t %T %X %Y %Z %W %o"
  set -u
}

acl_only() { awk '{print $1, $4, $5, $6}'; }
timestamp_only() { awk '{print $1, $12, $13, $14, $15}'; }
data_only() { awk '{print $1, $2, $3, $7, $8, $9, $10, $11, 16}'; }

git ls-tree -z --full-tree -r --name-only HEAD | grep -z -v -Ff $tmp_deleted | \
  get_metadata -0 > $tmp_metadata
git status -s | awk '$1=="??" {print $2}' | \
  get_metadata >> $tmp_metadata

#
# Sort
#
LC_ALL=C sort $tmp_metadata | uniq | \
    grep -vF "$tmp_metadata" |  grep -vF "$tmp_deleted" > $result_file

rm $tmp_metadata
rm $tmp_deleted

#
# Separate into ACL, Timestamps, and FS metadata
#

cat $result_file | acl_only > $result_acl_file
cat $result_file | timestamp_only > $result_timestamp_file
cat $result_file | data_only > $result_data_file
