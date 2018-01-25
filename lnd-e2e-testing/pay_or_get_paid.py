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

def run(cmd, timeout=600):
  return json.loads(
               subprocess.check_output(
                        cmd.split(' '),
                        timeout=timeout).decode("utf-8"))

def log(msg):
  timestamp = datetime.datetime.now()
  timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
  with open(LOGFILE, 'a') as w:
    w.write("{} {}\n".format(timestamp, msg))


class MySocket:
    """demonstration class only
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
x = 10
sat_paied = 0
sat_received = 0
drop = False

while True:
  if payee:
    invoice_list = []
    for _ in range(x):
      invoice = run('lncli addinvoice {}'.format(MICROPAYMENT))
      invoice_list.append(invoice)
      print("Sending invoice: {}".format(invoice))
      s.mysend(invoice['pay_req'])

    # Confirm that invoice was settled
    TOTAL_TIMEOUT = 600
    for seconds_passed in range(TOTAL_TIMEOUT): # TOTO: actually count seconds, not polls
      num_settled = 0
      for invoice in invoice_list:
        invoice_status = \
          run('lncli lookupinvoice {}'.format(invoice['r_hash']))
        if invoice_status['settled']:
          num_settled += 1

      print("{} of {} settled after {} seconds (timeout triggering a switch will be at {} seconds)".format(
            num_settled, len(invoice_list), seconds_passed, TOTAL_TIMEOUT))
      if num_settled == len(invoice_list):
        sat_received += (MICROPAYMENT * num_settled)
        break
      time.sleep(1)
    else:
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
    pay_req = s.myreceive()
    print("Got invoice: {}".format(pay_req))
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
      for _ in range(10):
        try:
          result = run('lncli payinvoice {}'.format(pay_req), timeout=60)
        except Exception as e:
          print(e)
        else:
          if result['payment_error'] == '':
            sat_paied += MICROPAYMENT
            break
          else:
            print("payinvoice FAILED: {}".format(result))
      else:
        print("Could not pay invoice {}, dropping all further invoces until 'switch'!".format(pay_req))
        drop = True
