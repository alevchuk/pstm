#!/usr/bin/python3

import time
import argparse
import socket
import subprocess
import json
import datetime
from os.path import expanduser
HOME = expanduser("~")

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', type=int, required=True)
parser.add_argument('-s', '--host', type=str)
parser.add_argument('-l', '--listen', action='store_true')

args = parser.parse_args()

MSGLEN = 400
LOGFILE = HOME + "/pay_or_get_paid.py.log"
GET_BALANCE = HOME + '/lnd-e2e-testing/get_balance_report.py'

RUN_TRY_NUM = 12
RUN_TRY_SLEEP = 10

def run(cmd, timeout=120):
  accumulated_timeout = 0
  for _ in range(RUN_TRY_NUM):
    try_start = time.time()
    try:
      raw = subprocess.check_output(
               cmd.split(' '),
               timeout=timeout
            ).decode("utf-8")
      break
    except Exception as e:
        print(e)
        print("Sleeping for {} seconds".format(RUN_TRY_SLEEP))
        time.sleep(RUN_TRY_SLEEP)

    try_duration = time.time() - try_start
    accumulated_timeout += try_duration

    if accumulated_timeout > timeout:
        raise Exception("Run command {} timeout after {} seconds".format(cmd, accumulated_timeout))

  else:
    raise Exception("Failed command: {}".format(cmd))

  return json.loads(raw)

def log(msg):
  timestamp = datetime.datetime.now()
  timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
  with open(LOGFILE, 'a') as w:
    msg = "{} {}\n".format(timestamp, msg)
    print(msg)
    w.write(msg)


class MySocket:
    """
      MySocket implementation from https://docs.python.org/2/howto/sockets.html#using-a-socket
      - coded for clarity, not efficiency
    """

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(
                            socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, host, port):
        self.sock.connect((host, port))

    @staticmethod
    def listen(port):
        #create an INET, STREAMing socket
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #bind the socket to a public host,
        # and a well-known port
        serversocket.bind((socket.gethostname(), port))
        #become a server socket
        serversocket.listen(5)

        return serversocket

    def mysend(self, msg):
        if len(msg) < MSGLEN:
          msg += ' ' * (MSGLEN - len(msg))

        totalsent = 0
        while totalsent < MSGLEN:
            sent = self.sock.send(bytes(msg[totalsent:], 'UTF-8'))
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def myreceive(self):
        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            chunk = self.sock.recv(min(MSGLEN - bytes_recd, 2048))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return (b''.join(chunks)).decode('UTF-8').strip()

if args.listen:
  serversocket = MySocket.listen(args.port)
  #accept connections from outside
  (clientsocket, address) = serversocket.accept()

  s = MySocket(clientsocket)
  ping = s.myreceive()
  assert ping == 'ping'
  s.mysend("pong")

  payee = False

else:
  s = MySocket()
  s.connect(args.host, args.port)
  s.mysend("ping")
  pong = s.myreceive()
  assert pong == 'pong'

  payee = True



MICROPAYMENT = 5867
NUM_PAYMENTS_PER_BATCH = 20
sat_paied = 0
sat_received = 0
drop = False
retry = False

while True:
  if payee:
    invoice_list = []
    for _ in range(NUM_PAYMENTS_PER_BATCH):
      invoice = run('lncli addinvoice {}'.format(MICROPAYMENT))
      invoice_list.append(invoice)
      print("Sending invoice: {}".format(invoice))
      s.mysend(invoice['pay_req'])

    # Confirm that invoice was settled
    TOTAL_TIMEOUT = 600
    start_time = time.time()
    all_settled = False
    for _ in range(TOTAL_TIMEOUT):
      num_settled = 0
      for invoice in invoice_list:
        invoice_status = \
          run('lncli lookupinvoice {}'.format(invoice['r_hash']))
        if invoice_status['settled']:
          num_settled += 1

      seconds_passed = time.time() - start_time
      if seconds_passed > TOTAL_TIMEOUT:
        log("Invoice check timeout after {} seconds".format(seconds_passed))
        break

      print("{} of {} settled after {} seconds (timeout triggering a switch will be at {} seconds)".format(
            num_settled, len(invoice_list), seconds_passed, TOTAL_TIMEOUT))
      if num_settled == len(invoice_list):
        sat_received += (MICROPAYMENT * num_settled)
        all_settled = True
        break

      time.sleep(1)

    if not all_settled:
      # not everything got payed, yet count any remaining invoices that were settled
      for invoice in invoice_list:
        invoice_status = \
          run('lncli lookupinvoice {}'.format(invoice['r_hash']))
        if invoice_status['settled']:
          sat_received += MICROPAYMENT

      print("Cannot settle after {}s, time to switch".format(seconds_passed))
      s.mysend("switch")

      log(json.dumps(run(GET_BALANCE + ' --json'), sort_keys=True))
      log("Switch. Total sat_received was {:,} ({:,} payments)".format(
        sat_received,
        sat_received / MICROPAYMENT))

      payee = False
      sat_paied = 0
      sat_received = 0

  else:

    if not retry:
        pay_req = s.myreceive()
        print("Got invoice: {}".format(pay_req))
    retry = False

    if pay_req == "switch":
      log(json.dumps(run(GET_BALANCE + ' --json'), sort_keys=True))
      log("Switch. Total sat_paied was {:,} ({:,} payments)".format(
        sat_paied,
        sat_paied / MICROPAYMENT))

      payee = True
      drop = False
      sat_paied = 0
      sat_received = 0
    elif drop:
        print("Dropping invoce {}".format(pay_req))
    else:

      try:
        result = run('lncli payinvoice {}'.format(pay_req), timeout=60)
      except Exception as e:
        print(e)
        print("payinvoice FAILED: {}, dropping all further invoces until 'switch'!".format(e))
        drop = True
      else:
        if result['payment_error'] == '':
          sat_paied += MICROPAYMENT
        else:
          # most likely BTCD is behind, try again in a little bit
          if result['payment_error'].startswith('FinalIncorrectCltvExpiry'):
            retry = True
          else:
            log("Could not pay invoice {} because {}, "
                  "dropping all further invoces until 'switch'!".format(
                      pay_req, result['payment_error']
                  )
              )
            drop = True
