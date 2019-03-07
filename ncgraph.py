import curses
import math

debugfile = open("debug.output", 'w')
def DEBUG(string):
    debugfile.write("%s\n" % string)

class DataSeries(object):
    def __init__(self, X, Y, label, color=0):
        assert (len(X) == len(Y))
        self.X = X.copy()
        self.Y = Y.copy()
        self.label = label
        self.length = len(X)
        self.color = color

class Grapher(object):
    seriesList = []
    legend = False
    colorList = [2, 3, 4, 5, 6, 7]
    autoAxis = True

    def __init__(self, window):
        # Setup the window
        self.setWindow(window)
        # Initalise color
        curses.start_color()
        curses.use_default_colors()
        for i in range(curses.COLORS):
            curses.init_pair(i+1, i, -1)

    def setWindow(self, window):
        self.plotArea = window # TODO: Setup boarders with plotArea
        self.height, self.width = self.plotArea.getmaxyx()

    def setAxis(self, x_min=0, x_max=0, y_min=0, y_max=0, auto=False):
        self.autoAxis = auto
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max

    """
    If self.autoAxis is True, scans all the data series in self.seriesList
    and determines x_min, x_max, y_min, y_max.
    """
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
            self.y_min = min(seriesYMins) - 0.1 * (max(seriesYMaxs) - min(seriesYMins))
            self.y_max = max(seriesYMaxs) + 0.1 * (max(seriesYMaxs) - min(seriesYMins))

    def autosize(self):
        self.autoAxis = True
        self.redraw()

    """
    The next x methods: quick and dirty resize and move.
    """
    def getxsize(self):
        center = (self.x_max + self.x_min) / 2
        size = self.x_max - self.x_min
        return (center, size)
    def setxsize(self, center, size):
        self.autoAxis = False
        self.x_max = center + size / 2
        self.x_min = center - size / 2
        self.redraw()

    def getysize(self):
        center = (self.y_max + self.y_min) / 2
        size = self.y_max - self.y_min
        return (center, size)
    def setysize(self, center, size):
        self.autoAxis = False
        self.y_max = center + size / 2
        self.y_min = center - size / 2
        self.redraw()

    def changex(self, relmove, relzoom):
        center, size = self.getxsize()
        center = center + relmove * size
        size = size * relzoom
        self.setxsize(center, size)
    def zoominx(self):
        self.changex(0, 3/4)
    def zoomoutx(self):
        self.changex(0, 4/3)
    def moveright(self):
        self.changex(.2, 1)
    def moveleft(self):
        self.changex(-.2, 1)

    def changey(self, relmove, relzoom):
        center, size = self.getysize()
        center = center + relmove * size
        size = size * relzoom
        self.setysize(center, size)
    def zoominy(self):
        self.changey(0, 3/4)
    def zoomouty(self):
        self.changey(0, 4/3)
    def moveup(self):
        self.changey(.2, 1)
    def movedown(self):
        self.changey(-.2, 1)

    """
    The next methods: Determine nice grid points
    """
    def getgridpoints(self, size, minNum, zmin, zmax):
        # maximum allowed distance between two grid points
        maxDistance = size / minNum
        maxMagnitude = math.log10(maxDistance)
        # upper = 100 or 1 or .00001 or something, but it's bigger than maxDistance,
        # so .1 * upper < maxDistance < upper
        upper = 10 ** math.ceil(maxMagnitude)
        upperMagnitude = upper
        candidates = [.5 * upper, .25 * upper, .2 * upper, .1 * upper]
        DEBUG("size = {}, maxdist = {}, upper = {}".format(size, maxDistance, upper))
        distance = None
        for candidate in candidates:
            if candidate < maxDistance:
                distance = candidate
                break
        if distance == None:
            raise Exception('There should be at least .1 * upperBound smaller than maxDistance!')
        # distance is now a value like 250, 1000, .5, .00002
        # now we have to find the values between min and max that match
        # divide the lower bound of the axis by the distance, ceil(), and add distance as long as we are smaller than the upper bound of the axis
        gridpoints = []
        point = math.ceil(zmin / distance) * distance
        while point < zmax:
            gridpoints.append(point)
            point = point + distance
        return gridpoints

    def getxgrid(self):
        center, size = self.getxsize()
        return self.getgridpoints(size, 2, self.x_min, self.x_max)
    def getygrid(self):
        center, size = self.getysize()
        return self.getgridpoints(size, 4, self.y_min, self.y_max)

    def plotGridlines(self):
        return
        xgrid = self.getxgrid()
        ygrid = self.getygrid()
        for x in xgrid:
            col = self.mapValue(x, self.x_min, self.x_max, 0, self.width-1)
            for row in range(0, self.height-1):
                self.plotArea.addstr(row, col, '|')
        for y in ygrid:
            # The first one works, too, but does not yield the same result as the x-axis so the gridline and x-axis don't match
            #row = self.mapValue(y, self.y_min, self.y_max, self.height-1, 0)
            row = self.height-1 - self.mapValue(y, self.y_min, self.y_max, 0, self.height-1)
        #xaxisy = self.height-1 - self.mapValue(0, self.y_min, self.y_max, 0, self.height-1)
            for col in range(0, self.width-1):
                self.plotArea.addstr(row, col, '-')
    
    def plotGrid(self):
        xgrid = self.getxgrid()
        ygrid = self.getygrid()
        for x in xgrid:
            col = self.mapValue(x, self.x_min, self.x_max, 0, self.width-1)
            text = str(x)
            self.plotArea.addstr(self.height-2, col, '┴')
            if col + len(text) > self.width-1:
                col = self.width-1 - len(text)
            self.plotArea.addstr(self.height-1, col, text)
        for y in ygrid:
            row = self.height-1 - self.mapValue(y, self.y_min, self.y_max, 0, self.height-1)
            self.plotArea.addstr(row, 6, '├')
            text = str(y)
            if len(text) > 5:
                text = text[0:5] + " "
            else:
                text = " " * (5-len(text)) + text + " "
            self.plotArea.addstr(row, 0, text)

    """
    Plots the coordinate system axis, the ordinate and abscissa.
    """
    # TODO If the coordinate base lies outside of the drawing area, what will happen?
    def plotAxis(self):
        # Calculate x, y values at y, x axis
        yaxisx = self.mapValue(0, self.x_min, self.x_max, 0, self.width-1)
        xaxisy = self.height-1 - self.mapValue(0, self.y_min, self.y_max, 0, self.height-1)
        # Plot y axis
        if self.isPlottable(0, self.y_min):
            for y in range(self.height):
                self.plotArea.addstr(y, yaxisx, "|")
            self.plotArea.addstr(0, yaxisx, "^") # arrow
        # Plot x axis
        if self.isPlottable(self.x_min, 0):
            for x in range(self.width):
                self.plotArea.addstr(xaxisy, x, "-")
            self.plotArea.addstr(xaxisy, self.width-1, ">") # arrow
        # Plot origin
        if self.isPlottable(0, 0):
            self.plotArea.addstr(xaxisy, yaxisx, "+")

    def toggleLegend(self):
        self.legend = not self.legend;
        self.redraw(); # this calls updateLegend(), too

    """
    If self.legend is True, plots a legend box in the upper right corner.
    """
    def updateLegend(self):
        if not self.legend:
            return
        y = 0
        labelLengths = []
        for ds in self.seriesList:
            labelLengths.append(len(ds.label))
        x = self.width - max(labelLengths)
        for ds in self.seriesList:
            self.plotArea.addstr(y, x, " "*max(labelLengths), curses.color_pair(ds.color) | curses.A_REVERSE)
            self.plotArea.addstr(y, x, ds.label, curses.color_pair(ds.color) | curses.A_REVERSE)
            y += 1

    """
    If we have the (x or y)-limits origin_start to origin_end and we print this
    on screen/window coordinates output_start (0) to output_end (width-1 / height-1),
    where do we have to print the value?
    """
    def mapValue(self, value, origin_start, origin_end, output_start, output_end):
        origin_proportion = (value - origin_start) / (origin_end - origin_start)
        output_proportion = origin_proportion * (output_end - output_start)
        return int(output_start + output_proportion)

    """
    Checks whether a given (x,y) is inside the drawing area.
    """
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
        if (not plottable) and self.autoAxis:
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
                    #self.plotArea.addstr(py, px, " ", curses.color_pair(ds.color) | curses.A_REVERSE)
                    self.plotArea.addstr(py, px, "*", curses.color_pair(ds.color))

    def clearPlotArea(self):
        self.plotArea.addstr(0, 0, " ")
        self.plotArea.clrtobot()

    def clearData(self):
        self.seriesList = []

    def plot(self, X, Y, label="myData"):
        # Add the new data to the seriesList.
        self.seriesList.append(DataSeries(X, Y, label, color=self.colorList[len(self.seriesList)]))
        self.redraw()

    def redraw(self):
        # Determine the new size of the plotting area
        self.height, self.width = self.plotArea.getmaxyx()
        # Clear the screen of any current plots.
        self.clearPlotArea()
        # Update axis limits
        self.updateAxis()
        # Plot the background grid lines
        self.plotGridlines()
        # Plot axis lines
        self.plotAxis()
        # Re-plot each DataSeries.
        self.plotAll()
        # Plot the grid points
        self.plotGrid()
        # Update the legend.
        self.updateLegend()

if __name__ == '__main__':
    import numpy
    import math

    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()

    x, y = [], []
    x = [i for i in numpy.arange(-3.5, 3.5, 0.01)]
    ya = [math.sin(i) for i in x]
    yb = [(1/4)*math.sin(4*i) for i in x]
    yc = [math.sin(i) + (1/4)*math.sin(4*i) for i in x]
    myGrapher = Grapher(stdscr)
    myGrapher.plot(x, ya, label="sin(x)")
    myGrapher.plot(x, yb, label="(1/4)sin(4x)")
    myGrapher.plot(x, yc, label="sin(x)+(1/4)sin(4x)")

    stdscr.getch()

    curses.echo()
    curses.nocbreak()
    curses.endwin()
