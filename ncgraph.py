import curses

debugfile = open("debug.output", 'w')
def DEBUG(string):
    debugfile.write("%s\n" % string)

class DataSeries(object):
    def __init__(self, X, Y, label):
        assert (len(X) == len(Y))
        self.X = X.copy()
        self.Y = Y.copy()
        self.label = label
        self.length = len(X)

class Grapher(object):
    seriesList = []
    legend = False

    def __init__(self, window):
        self.setWindow(window)

    def setWindow(self, window):
        self.window = window
        self.plotArea = window # TODO: Setup boarders with plotArea
        self.height, self.width = self.window.getmaxyx()

    def setAxis(self, x_min=0, x_max=0, y_min=0, y_max=0, auto=False):
        self.autoAxis = auto
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max

    def updateAxis(self):
        if self.autoAxis:
            seriesXMins = []
            seriesXMaxs = []
            seriesYMins = []
            seriesYMaxs = []
            for ds in self.seriesList:
                seriesXMins.append(min(ds.X))
                seriesXMaxs.append(max(ds.X))
                DEBUG("Series XMax %f" % max(ds.X))
                seriesYMins.append(min(ds.Y))
                seriesYMaxs.append(max(ds.Y))
            self.x_min = min(seriesXMins)
            self.x_max = max(seriesXMaxs)
            self.y_min = min(seriesYMins)
            self.y_max = max(seriesYMaxs)
            DEBUG("NOTE x_min:%f" % self.x_min)
            DEBUG("NOTE x_max:%f" % self.x_max)
            DEBUG("NOTE y_min:%f" % self.y_min)
            DEBUG("NOTE y_max:%f" % self.y_max)
            for i in seriesXMaxs:
                DEBUG("NOTE SXM %f" % (i))
        self.plotAxis()

    def plotAxis(self):
        # Calculate x, y values at y, x axis
        xaty = self.mapValue(0, self.x_min, self.x_max, 0, self.width-1)
        yatx = self.height-1 - self.mapValue(0, self.y_min, self.y_max, 0, self.height-1)
        # Plot x, y axis and the origin.
        for y in range(self.height):
            self.plotArea.addstr(y, xaty, "|")
        for x in range(self.width):
            self.plotArea.addstr(yatx, x, "-")
        self.plotArea.addstr(yatx, xaty, "+")
        # Add arrows
        self.plotArea.addstr(yatx, self.width-1, ">")
        self.plotArea.addstr(0, xaty, "^")

    def toggleLegend(self):
        self.legend = not self.legend;
        self.updateLegend();

    def updateLegend(self):
        pass

    def mapValue(self, value, origin_start, origin_end, output_start, output_end):
        origin_proportion = (value - origin_start) / (origin_end - origin_start)
        output_proportion = origin_proportion * (output_end - output_start)
        return int(output_start + output_proportion)

    def isPlottable(self, x, y):
        plottable = True
        if (x < self.x_min):
            plottable = False
        if (x > self.x_max):
            plottable = False
        if (y < self.y_min):
            plottable = False
        if (y > self.y_max):
            plottable = False
        if (not plottable) and autoAxis:
            DEBUG("ERR not plottable during autoaxis!!")
        return plottable

    def plotAll(self):
        # TODO: Currently Raster, make Vector.
        for ds in self.seriesList:
            DEBUG("NOTE ds.length %i" % ds.length)
            for i in range(ds.length):
                x, y = ds.X[i], ds.Y[i]
                # Check the value lies in the plottable area.
                if self.isPlottable(x, y):
                    # The value is plottable, map it to a (px, py) plot location.
                    px = self.mapValue(x, self.x_min, self.x_max, 0, self.width-1)
                    py = self.height-1 - self.mapValue(y, self.y_min, self.y_max, 0, self.height-1)
                    # Plot the point at that location.
                    self.plotArea.addstr(py, px, "#")

    def clearPlotArea(self):
        self.plotArea.addstr(0, 0, " ")
        self.plotArea.clrtobot()

    def clearData(self):
        self.seriesList = []

    def plot(self, X, Y, label="myData"):
        # Add the new data to the seriesList.
        self.seriesList.append(DataSeries(X, Y, label))
        # Clear the screen of any current plots.
        self.clearPlotArea()
        # Update and plot the axis.
        self.updateAxis()
        # Re-plot each DataSeries.
        self.plotAll()
        # Update the legend.
        self.updateLegend()

import numpy
import math

stdscr = curses.initscr()
curses.noecho()
curses.cbreak()

x, y = [], []
for i in numpy.arange(0, 360, 0.25):
    j = math.cos((i/180) * math.pi)
    x.append(i)
    y.append(j)

myGrapher = Grapher(stdscr)
myGrapher.setAxis(auto=True)
myGrapher.plot(x, y, label="cos(x) for 0<x<360")

stdscr.getch()

for i in range(len(x)): x[i] = (-x[i])
myGrapher.plot(x, y, label="cos(-x) for 0<x<360")

stdscr.getch()

curses.echo()
curses.nocbreak()
curses.endwin()
