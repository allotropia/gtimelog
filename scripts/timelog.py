#!/usr/bin/python

from __future__ import print_function

import datetime
import readline

with open("timelog.txt", "a") as f:
    print("", file=f)

while True:
    try:
        what = input("> ")
    except EOFError:
        print()
        break
    ts = datetime.datetime.now()
    line = "%s: %s" % (ts.strftime("%Y-%m-%d %H:%M"), what)
    print(line)
    with open("timelog.txt", "a") as f:
        print(line, file=f)
