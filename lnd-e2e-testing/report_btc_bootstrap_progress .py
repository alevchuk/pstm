#!/usr/bin/python3

import re
import typing
import datetime
import sys

from os.path import expanduser
home = expanduser("~")

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
