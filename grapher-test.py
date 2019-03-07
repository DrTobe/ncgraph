#!/usr/bin/python

import ncgraph
import numpy
import math

import curses
from curses import wrapper

def main(stdscr):
    stdscr.clear()
    curses.curs_set(False)

    x, y = [], []
    x = [i for i in numpy.arange(-3.5, 13.5, 0.01)]
    ya = [math.sin(i) for i in x]
    yb = [(1/4)*math.sin(4*i) for i in x]
    yc = [math.sin(i) + (1/4)*math.sin(4*i) for i in x]
    myGrapher = ncgraph.Grapher(stdscr)
    myGrapher.plot(x, ya, label="sin(x)")
    myGrapher.plot(x, yb, label="(1/4)sin(4x)")
    myGrapher.plot(x, yc, label="sin(x)+(1/4)sin(4x)")

    colornum = 0
    while True:
        # Test colors
        if False:
            colornum = (colornum + 1) % curses.COLORS
            curses.init_pair(10, colornum, 0)
            text = str(colornum) + " " + str(curses.COLOR_PAIRS) + " " + str(curses.can_change_color())
            stdscr.addstr(0,0, text, curses.color_pair(10))
        # Input handling
        k = stdscr.getkey()
        if k == 'q':
            break
        elif k == 'r':
            myGrapher.redraw()
        elif k == 'g':
            myGrapher.toggleLegend()
        elif k == 't':
            myGrapher.toggleTicks()
        elif k == 'l':
            myGrapher.moveright()
        elif k == 'h':
            myGrapher.moveleft()
        elif k == 'j':
            myGrapher.movedown()
        elif k == 'k':
            myGrapher.moveup()
        elif k == 'w':
            myGrapher.zoominy()
        elif k == 's':
            myGrapher.zoomouty()
        elif k == 'a':
            myGrapher.zoomoutx()
        elif k == 'd':
            myGrapher.zoominx()
        elif k == 'x':
            myGrapher.autosize()
        else:
            stdscr.addstr(0,0,k)


wrapper(main)
