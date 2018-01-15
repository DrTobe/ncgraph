import curses as c

debugfile = open("debug.output", 'w')
def debug(string):
    debugfile.write("%s\n" % string)

class ncgrapher(object):
    class color(object):
        red = 197
        blue = 22
        magenta = 200
    def __init__(self, window):
        # Note the window we're operating in.
        self.updateWindow(window);
        # Set some curses rules we need
        c.noecho()
        c.cbreak()
        # Setup curses color
        c.start_color()
        c.use_default_colors()
        for i in range(0, c.COLORS):
            c.init_pair(i+1, i, -1)
    def updateWindow(self, window):
        # Set to a new window area.
        self.window = window;
        # Get the dimentions of the window we're working with.
        self.height, self.width = window.getmaxyx()
    def map(self, v, a, b, x, y):
        # Maps a value from one range to another
        return int((((v-a)/(b-a))*(y-x))+x)
    def plot(self, X, Y, color=0):
        # Get metadata from data
        xmax = max(X)
        xmin = min(X)
        ymax = max(Y)
        ymin = min(Y)
        length = len(X)
        # Plot the Axis
        xaty = self.map(0, xmin, xmax, 0, self.width-1)
        for y in range(self.height):
            self.window.addstr(y, xaty, "|")
        yatx = self.map(0, ymin, ymax, 0, self.height-1)
        for x in range(self.width):
            self.window.addstr(yatx, x, "-")
        self.window.addstr(yatx, xaty, "+")
        # Plot the data
        for d in range(length):
            px, py = X[d], Y[d]
            gx = self.map(px, xmin, xmax, 0, self.width-1)
            gy = (self.height-1) - self.map(py, ymin, ymax, 0, self.height-1)
            debug("gx:%i gy:%i" % (gx, gy))
            self.window.addstr(gy, gx, "#", c.color_pair(color))
    def clear(self):
        self.window.addstr(0,0," ")
        self.window.clrtobot()
    def end(self):
        c.nocbreak()
        c.echo()
        c.endwin()

import numpy as np
import math

stdscr = c.initscr()
g = ncgrapher(stdscr)

i = 0
while (1):
    sx, sy = [], []
    cx, cy = [], []
    i += 10
    for xp in np.arange(0, 360, 0.25):
        yp = math.sin((xp/180) * math.pi + i/180)
        sx.append(xp)
        sy.append(yp)
        yp = math.cos((xp/180) * math.pi - i/180)
        cx.append(xp)
        cy.append(yp)

    g.clear()
    g.plot(sx, sy, color=g.color.blue)
    g.plot(cx, cy, color=g.color.red)
    stdscr.getch()
g.end()
