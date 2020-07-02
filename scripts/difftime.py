#!/usr/bin/python

from __future__ import print_function

import readline

def parse_time(s):
    h, m = list(map(int, s.strip().split(':')))
    return h * 60 + m

def fmt_delta(mins):
    sign = mins < 0 and "-" or ""
    mins = abs(mins)
    if mins >= 60:
        h = mins / 60
        m = mins % 60
        return "%s%d min (%d hr, %d min)" % (sign, mins, h, m)
    else:
        return "%s%d min" % (sign, mins)

while True:
    try:
        what = input("start, end> ")
    except EOFError:
        print()
        break
    try:
        if ',' in what:
            t1, t2 = list(map(parse_time, what.split(',')))
        else:
            t1, t2 = list(map(parse_time, what.split()))
        print(fmt_delta(t2 - t1))
    except ValueError:
        print(eval(what))

