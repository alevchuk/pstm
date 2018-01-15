#!/usr/bin/python3

import re
import typing
import datetime
import sys

from os.path import expanduser
home = expanduser("~")

# # Example output:
# 2018-01-12T00:37:18.936000      ************************        120,355 blocks  86d     (2015-03-07 08:55:45+00:00 - 2015-06-01 11:06:10+00:00)
# 2018-01-12T04:37:18.936000      ********                        40,543 blocks   29d     (2015-06-01 18:04:53+00:00 - 2015-07-01 01:47:51+00:00)
# 2018-01-12T08:37:18.936000      ****                            20,897 blocks   20d     (2015-07-01 04:12:19+00:00 - 2015-07-21 09:04:16+00:00)
# 2018-01-12T12:37:18.936000      *****                           25,412 blocks   38d     (2015-07-21 12:06:55+00:00 - 2015-08-28 02:16:57+00:00)
# 2018-01-12T16:37:18.936000      *********                       45,838 blocks   55d     (2015-08-28 05:14:03+00:00 - 2015-10-22 04:26:26+00:00)
# 2018-01-12T20:37:18.936000      ****                            21,458 blocks   20d     (2015-10-22 05:00:52+00:00 - 2015-11-11 02:26:26+00:00)
# 2018-01-13T00:37:18.936000                                      4,725 blocks    7d      (2015-11-11 02:49:48+00:00 - 2015-11-18 09:47:33+00:00)
# 2018-01-13T04:37:18.936000                                      1,967 blocks    14d     (2015-11-18 14:14:15+00:00 - 2015-12-02 10:43:35+00:00)
# 2018-01-13T08:37:18.936000      ***                             17,898 blocks   13d     (2015-12-02 13:27:31+00:00 - 2015-12-15 07:06:11+00:00)
# 2018-01-13T12:37:18.936000                                      858 blocks      9d      (2015-12-15 07:27:00+00:00 - 2015-12-24 10:22:09+00:00)
# 2018-01-13T16:37:18.936000      *                               7,967 blocks    25d     (2015-12-24 11:31:37+00:00 - 2016-01-18 21:36:08+00:00)
# 2018-01-13T20:37:18.936000      *****************               86,407 blocks   44d     (2016-01-18 21:43:43+00:00 - 2016-03-02 13:56:52+00:00)
# 2018-01-14T00:37:18.936000      *****                           29,180 blocks   26d     (2016-03-02 14:39:54+00:00 - 2016-03-28 16:16:47+00:00)
# 2018-01-14T04:37:18.936000      ******************************  146,506 blocks  114d    (2016-03-28 22:26:51+00:00 - 2016-07-21 04:08:07+00:00)
# 2018-01-14T08:37:18.936000      *************                   66,823 blocks   71d     (2016-07-21 10:39:15+00:00 - 2016-09-30 15:11:41+00:00)
# 2018-01-14T12:37:18.936000      *********                       46,760 blocks   24d     (2016-09-30 15:32:06+00:00 - 2016-10-25 01:35:54+00:00)
# 2018-01-14T16:37:18.936000      *********                       44,097 blocks   44d     (2016-10-25 01:42:23+00:00 - 2016-12-08 07:31:09+00:00)
# 2018-01-14T20:37:18.936000                                      2,277 blocks    5d      (2016-12-08 07:59:35+00:00 - 2016-12-13 12:50:53+00:00)
# 2018-01-15T00:37:18.936000      *******************             96,712 blocks   229d    (2016-12-13 13:56:48+00:00 - 2017-07-30 08:32:15-07:00)
# 2018-01-15T04:37:18.936000      *************                   65,946 blocks   95d     (2017-07-30 14:51:51-07:00 - 2017-11-02 18:13:40-07:00)

def visual_int(number, upper_limit):
    width = 30
    ratio = number / upper_limit
    dots = width * ratio
    return "*" * int(dots) + " " * (width - int(dots))


block_processed_re = re.compile(
    "(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d+.\d+) \[INF\] SYNC: Processed (\d+) blocks in the last .+s \(\d+ transactions, height \d+, (.*)\)")

Bucket = typing.NamedTuple('Bucket', [
    ['event_time', datetime.datetime],
    ['min_block_time', datetime.datetime],
    ['max_block_time', datetime.datetime],
    ['sum_blocks', int]])

buckets = []
if len(sys.argv) > 1:
    bucket_size = datetime.timedelta(hours=int(sys.argv[1]))
else:
    bucket_size = datetime.timedelta(hours=4)
    
bucket_start = None
min_block_time = None
max_block_time = None
sum_blocks = 0

max_blocks_in_window = 0

# skip everything before this block time
start_time = datetime.datetime.strptime("2015-03-07 08:55:45 +0000 UTC", "%Y-%m-%d %H:%M:%S %z %Z")

# i switched system timezone, so this messed up the timestamps in the logs half way through
tz_switch_time = '2018-01-15 04:56:09.353'
tz_offset_hours = datetime.timedelta(hours=-8)

with open(home + '/.btcd/logs/testnet/btcd.log') as f:
    for line in f:
        m = re.match(block_processed_re, line)
        if m:
            # fix tz switch
            if m.group(1) == '2018-01-15 04:56:09.353':
                tz_offset_hours = datetime.timedelta(hours=0)

            # 2018-01-15 03:48:13.899
            processing_time = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S.%f")
            processing_time += tz_offset_hours

            # Num blocks
            num_blocks = int(m.group(2))

            # 2016-12-05 14:18:43 +0000 UTC
            block_time = datetime.datetime.strptime(m.group(3), "%Y-%m-%d %H:%M:%S %z %Z")

            # spkip
            if block_time < start_time:
                continue

            if bucket_start is None:
               bucket_start = processing_time
               min_block_time = block_time
               max_block_time = block_time
               sum_blocks = num_blocks

            if processing_time > bucket_start + bucket_size:
               # end of bucket time window
               buckets.append(Bucket(
                    event_time=bucket_start,
                    min_block_time=min_block_time,
                    max_block_time=max_block_time,
                    sum_blocks=sum_blocks))

               if sum_blocks > max_blocks_in_window:
                   max_blocks_in_window = sum_blocks

               bucket_start += bucket_size
               min_block_time = block_time
               max_block_time = block_time
               sum_blocks = num_blocks
            else:
                # still in the time bucket
                if block_time < min_block_time:
                    min_block_time = block_time

                if block_time > max_block_time:
                    max_block_time = block_time

                sum_blocks += num_blocks

for b in buckets:
    block_delta = (b.max_block_time - b.min_block_time).total_seconds() / (3600 * 24)
    print("{}\t{}\t{:,} blocks\t{:,.0f}d\t({} - {})".format(
            b.event_time.isoformat(),
            visual_int(b.sum_blocks, max_blocks_in_window),
            b.sum_blocks,
            block_delta,
            b.min_block_time,
            b.max_block_time))
