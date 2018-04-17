#!/usr/bin/python

from __future__ import print_function

import datetime
import readline

f = open("timelog.txt", "a")
print(file=f)
f.close()

while True:
    try:
        what = raw_input("> ")
    except EOFError:
        print()
        break
    ts = datetime.datetime.now()
    line = "%s: %s" % (ts.strftime("%Y-%m-%d %H:%M"), what)
    print(line)
    f = open("timelog.txt", "a")
    print(line, file=f)
    f.close()

