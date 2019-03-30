import curses
import math
import numpy

# Just for reference: Unicode box-drawing characters
# ─│┌┐└┘├┤┬┴┼

LEFTBORDER = 7
BOTTOMBORDER = 2

debug_file = open("debug.output", 'w')
def DEBUG(string):
    debug_file.write("%s\n" % string)

class DataSeries(object):
    def __init__(self, X, Y, label, color=0):
        assert (len(X) == len(Y))
        self.X = X.copy()
        self.Y = Y.copy()
        self.label = label
        self.length = len(X)
        self.color = color

# TODO Currently unused
class Lim(object):
    def __init__(self, lower, upper):
        self.set(lower, upper)
    def set(self, lower, upper):
        self.lower = lower
        self.upper = upper
    def range(self):
        return self.upper - self.lower

class Interval(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b
    """
    Checks if the interval contains the point/value p.
    """
    def contains(self, p):
        # As an interval could be decreasing, there are two possible cases how an interval
        # could contain a value. We have to test them both here.
        return (p >= self.a and p <= self.b) or (p <= self.a and p >= self.b)
    """
    Returns a (increasing) list of all integer values between a and b plus a and b themselves.
    As the interval could be defined with a > b and the returned list here is always increasing,
    the direction could be inverted.
    """
    def arange(self):
        # The rounding operations are required for range() to work. The direction of rounding
        # is determined so that the range does NOT contain the values themselves so that they
        # can be appended afterwards.
        if self.a < self.b:
            a,b = self.a, self.b
        else:
            a,b = self.b, self.a
        return [a] + list(range(math.floor(a)+1, math.floor(b))) + [b]
        

""" 
Returns the point of intersection of the lines passing through a2,a1 and b2,b1.
a1: [x, y] a point on the first line
a2: [x, y] another point on the first line
b1: [x, y] a point on the second line
b2: [x, y] another point on the second line
"""
# Inspired by / Taken from https://stackoverflow.com/a/42727584/805673
# Returns errorcode, x, y; errorcode == 0 if successful.
# After calculating the intersection of the two lines, we additionally check
# if this is a valid intersection for the two line segments, i.e. check if the
# found point is between the two points of each line segment.
def get_intersectBak(a1, a2, b1, b2):
    s = numpy.vstack([a1,a2,b1,b2])        # s for stacked
    h = numpy.hstack((s, numpy.ones((4, 1)))) # h for homogeneous
    l1 = numpy.cross(h[0], h[1])           # get first line
    l2 = numpy.cross(h[2], h[3])           # get second line
    x, y, z = numpy.cross(l1, l2)          # point of intersection
    if z == 0:                          # lines are parallel
        return -1, None, None
    x,y = (x/z, y/z) # The points are defined as (x, y, 1)
    # Now check if the point we have found is on the two line segments
    # The following check is not safe because of numeric issues (especially for horizontal and vertical lines)
    #if Interval(a1[0], a2[0]).contains(x) \
    #        and Interval(b1[0], b2[0]).contains(x) \
    #        and Interval(a1[1], a2[1]).contains(y) \
    #        and Interval(b1[1], b2[1]).contains(y):
    #            return 0, x, y
    # Instead, let's check if we have to move something between 0% and 100% of the
    # distance between two points:
    # The point we found is the point of a line segment plus a relative amount t of the
    # connection vector to the other point of that line segment:
    # (x,y) = a1 + (a2-a1) * t
    # (x,y) - a1 = (a2-a1) * t
    b = numpy.array([x-a1[0], y-a1[1]])
    A = numpy.array([[a2[0]-a1[0]], [a2[1]-a1[1]]])
    t = numpy.linalg.lstsq(A, b, rcond=None)[0][0] # First index for return-struct-unpacking, second for solution-indexing
    if Interval(0,1).contains(t):
        return 0, x, y
    else:
        return -1, None, None

def get_intersect(a1, a2, b1, b2):
    # v = vector from p1 to p2
    # line segment = p1 + v * [0..1]
    a = numpy.array(a1).reshape(2,1)
    a2 = numpy.array(a2).reshape(2,1)
    b = numpy.array(b1).reshape(2,1)
    b2 = numpy.array(b2).reshape(2,1)
    va = a2 - a
    vb = b2 - b
    #    a + va * ta = b + vb * tb
    # => a - b = vb * tb - va * ta
    # => a - b = (vb, -va) * (tb ta)^T = A * (tb ta)^T
    A = numpy.hstack((vb, -va))
    t, residuals, rank, singularvals = numpy.linalg.lstsq(A, a-b, rcond=None)
    if rank < 2:
        return -1, None, None
    i = Interval(0,1)
    if i.contains(t[0]) and i.contains(t[1]):
        p = a + va * t[1]
        return 0, p[0,0], p[1,0] # p.shape == (2,1) (it's 2D)
    return -1, None, None

class Mapping(object):
    def __init__(self, x_from, x_to, hbin_from, hbin_to, y_from, y_to, vbin_from, vbin_to):
        self.x_from = x_from
        self.x_to = x_to
        self.y_from = y_from
        self.y_to = y_to
        self.hbin_from = hbin_from
        self.hbin_to = hbin_to
        self.vbin_from = vbin_from
        self.vbin_to = vbin_to
        self.hbins_per_x = (hbin_to - hbin_from) / (x_to - x_from)
        self.vbins_per_y = (vbin_to - vbin_from) / (y_to - y_from)

    def map(self, x, y, rounding=True):
        return self.mapx(x, rounding), self.mapy(y, rounding)
    def mapx(self, x, rounding=True):
        # The nice thing about these mappings is that if any direction is reversed, this
        # effect is automatically fixed by the quotient hbins_per_x.
        # For example, if the x-direction is reversed (i.e. x_from > x_to), the denominator of
        # hbins_per_x is negative. Then, for any valid/fitting x, (x - self.x_from) is negative,
        # too. The result of the division indicates which fraction of the whole hbin-interval we
        # have to advance. The same holds true for the bin indexes.
        # Therefore, we can ignore the directions of x, h, y and v here.
        res = (x - self.x_from) * self.hbins_per_x + self.hbin_from
        if rounding:
            res = numpy.round(res)
            res = res.astype(int)
        return res
    def mapy(self, y, rounding=True):
        res = (y - self.y_from) * self.vbins_per_y + self.vbin_from
        if rounding:
            res = numpy.round(res)
            res = res.astype(int)
        return res

    def fits(self, x, y):
        return self.fitsx(x) and self.fitsy(y)
    def fitsx(self, x):
        return Interval(self.x_from, self.x_to).contains(x)
    def fitsy(self, y):
        return Interval(self.y_from, self.y_to).contains(y)

    def nofit(self, x, y):
        # Ensure that we are working on arrays
        x = numpy.array(x)
        y = numpy.array(y)
        # Determine left, right, top, bottom borders which is dependent on the ordering of
        # the from-to-values
        left = min(self.x_from, self.x_to)
        right = max(self.x_from, self.x_to)
        bottom = min(self.y_from, self.y_to)
        top = max(self.y_from, self.y_to)
        # For each border, determine if the value does not fit because it has crossed out
        # of the drawing area at that border
        outside = (x < left) * 1
        outside |= (x > right) * 2
        outside |= (y < bottom) * 4
        outside |= (y > top) * 8
        return outside


    def mapLine(self, x_start, y_start, x_end, y_end):
        # We have to draw something on the screen if either both points are in the plottable area
        # or at least one point is in the plottable area (then, we need to determine the intersection
        # with the bounding-box of the drawing area to know the point the line will be connected to).
        # But in fact, there is a third possibility: If none of the points is in the drawing area,
        # there could be two intersections with the bounding-box (like the line entering and leaving
        # the area) and we would have to draw the connection between these two intersections.
        # Summarizing, the sum of points in the drawing area and the number of intersections with the
        # bounding box need to be 2.
        # Due to numeric issues, values can be in the drawing area AND intersect with the borders.
        # Therefore, we collect the values in a set() after mapping. After mapping, the intersection
        # and the point itself will most probably be the same and not be added twice to the set.
        mapping_points = set()
        # First, check for the two points if they are in the drawing area
        xlim = Interval(self.x_from, self.x_to)
        ylim = Interval(self.y_from, self.y_to)
        if self.fits(x_start, y_start):
            mapping_points.add(self.map(x_start, y_start))
        if self.fits(x_end, y_end):
            mapping_points.add(self.map(x_end, y_end))
        # Now, check for intersections with the drawing area bounding box, for speedup only check
        # if more points are missing.
        if len(mapping_points) != 2:
            a = (x_start, y_start)
            b = (x_end, y_end)
            c0 = (self.x_from, self.y_from) # corner point, lower left
            c1 = (self.x_from, self.y_to) # upper left
            c2 = (self.x_to, self.y_to) # upper right
            c3 = (self.x_to, self.y_from) # lower right
            error, x, y = get_intersect(a, b, c0, c1)
            if not error:
                mapping_points.add(self.map(x,y))
            error, x, y = get_intersect(a, b, c1, c2)
            if not error:
                mapping_points.add(self.map(x,y))
            error, x, y = get_intersect(a, b, c2, c3)
            if not error:
                mapping_points.add(self.map(x,y))
            error, x, y = get_intersect(a, b, c3, c0)
            if not error:
                mapping_points.add(self.map(x,y))

        # Now, if we have exactly two mapping points, we will go on
        if len(mapping_points) != 2:
            return []
        # Now, continuing with a list so that we can consider one point the start
        # and the other point the end of the line segment.
        mapping_points = list(mapping_points)

        # For the sampling points of the mapping, we determine if it is a flat or a steep line
        # (with respect to the mapped bins).
        # If it is steep, we use all integers in the y-interval; if it is flat, use the x-interval. This
        # prevents us from having a non-continuous line or even no line at all, imagine a completely vertical
        # line ...
        DEBUG("mapping_points: {}".format(str(mapping_points)))
        #ah, av = self.map(mapping_points[0][0], mapping_points[0][1], rounding=False)
        #bh, bv = self.map(mapping_points[1][0], mapping_points[1][1], rounding=False)
        ah, av = mapping_points[0][0], mapping_points[0][1]
        bh, bv = mapping_points[1][0], mapping_points[1][1]
        if bv-av == 0 and bh-ah == 0:
            return []
        is_steep = (bh-ah == 0) or (abs((bv-av)/(bh-ah)) > 1)
        DEBUG(str(is_steep))
        if is_steep: # swap horizontal and vertical for the following calculations (straight line equation)
            ah, av, bh, bv = av, ah, bv, bh
        slope = (bv-av) / (bh-ah)
        line = []
        for h in Interval(ah, bh).arange():
            v = (h-ah) * slope + av
            h, v = int(round(h)), int(round(v))
            point = (h,v) if not is_steep else (v,h)
            line.append(point)
        return line


class Grapher(object):
    seriesList = []
    legend = False
    colorList = [2, 3, 4, 5, 6, 7]
    autoAxis = True
    draw_lines = True

    def __init__(self, window):
        # Reset seriesList for consecutive calls
        self.seriesList = []
        # Initialize borders
        self.border_left = LEFTBORDER
        self.border_bottom = BOTTOMBORDER
        # Setup the window
        self.setWindow(window)
        # Initalise color
        curses.start_color()
        curses.use_default_colors()
        for i in range(curses.COLORS):
            curses.init_pair(i+1, i, -1)

    def setWindow(self, window):
        self.window = window # TODO: Setup borders with window
        self.getPlotArea()

    def getPlotArea(self):
        self.height, self.width = self.window.getmaxyx()
        self.left = self.border_left
        self.right = self.width-1
        self.top = 0
        self.bottom = self.height-1-self.border_bottom

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
        return self.getgridpoints(size, 3, self.y_min, self.y_max)

    def plotGridlines(self):
        return # TODO deactivated until we have nicer color support
        xgrid = self.getxgrid()
        ygrid = self.getygrid()
        for x in xgrid:
            col = self.mapx(x)
            for row in range(self.top, self.bottom):
                self.window.addstr(row, col, '|') # TODO Replace by unicode box-drawing character
        for y in ygrid:
            row = self.mapy(y)
            for col in range(self.left, self.right):
                self.window.addstr(row, col, '-') # TODO see above
    
    def plotGrid(self):
        if not self.border_bottom or not self.border_left:
            return
        xgrid = self.getxgrid()
        ygrid = self.getygrid()
        for col in range(self.left, self.right+1):
            self.window.addstr(self.bottom+1, col, '─')
        for row in range(self.top, self.bottom+1):
            self.window.addstr(row, self.left-1, '│')
        self.window.addstr(self.bottom+1, self.left-1, '└')
        for x in xgrid:
            col = self.mapping.mapx(x)
            text = str(x)
            self.window.addstr(self.bottom+1, col, '┴') # self.bottom+1 == self.height-2 (line before last line)
            if col + len(text) > self.width-1:
                col = self.width-1 - len(text)
            self.window.addstr(self.bottom+2, col, text) # self.bottom+2 == self.height-1 (last line)
        for y in ygrid:
            row = self.mapping.mapy(y)
            self.window.addstr(row, self.border_left-1, '├')
            text = str(y)
            # The left-border text length should be <= border_left-1 --> len <= border_left-2 + " "
            if len(text) > self.border_left-2:
                text = text[0:self.border_left-2] + " "
            else:
                text = " " * (self.border_left-2-len(text)) + text + " "
            self.window.addstr(row, 0, text)

    """
    Plots the coordinate system axis, the ordinate and abscissa.
    """
    # TODO If the coordinate base lies outside of the drawing area, what will happen?
    def plotAxis(self):
        # Calculate x, y values at y, x axis
        centercol, centerrow = self.mapping.map(0, 0)
        # Plot y axis
        if self.mapping.fitsx(0):
            for row in range(self.top, self.bottom+1):
                self.window.addstr(row, centercol, "│")
            self.window.addstr(self.top, centercol, "↑") # arrow
        # Plot x axis
        if self.mapping.fitsy(0):
            for col in range(self.left, self.right+1):
                self.window.addstr(centerrow, col, "─")
            self.window.addstr(centerrow, self.right, "→") # arrow
        # Plot origin
        if self.mapping.fits(0, 0):
            self.window.addstr(centerrow, centercol, "┼")

    def toggleLegend(self):
        self.legend = not self.legend
        self.redraw() # this calls updateLegend(), too

    def toggleTicks(self):
        if self.border_left and self.border_bottom:
            self.border_left = 0
            self.border_bottom = 0
        else:
            self.border_left = LEFTBORDER
            self.border_bottom = BOTTOMBORDER
        self.redraw()

    def toggleLines(self):
        self.draw_lines = not self.draw_lines
        self.redraw()

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
        x = self.right+1 - max(labelLengths)
        for ds in self.seriesList:
            self.window.addstr(y, x, " "*max(labelLengths), curses.color_pair(ds.color) | curses.A_REVERSE)
            self.window.addstr(y, x, ds.label, curses.color_pair(ds.color) | curses.A_REVERSE)
            y += 1

    def updateMapping(self):
        self.mapping = Mapping(self.x_min, self.x_max, self.left, self.right, self.y_min, self.y_max, self.bottom, self.top)

    def plotAll(self):
        # The naive approach here is to plot all lines between data points first (so that they
        # end up in the background) and then plot all data points on top of them. This works but
        # slows down the application if there are a lot of data points involved. Maybe, this is
        # due to the fact that for each connection line, we have to determine if it will be drawn
        # which is done by checking if the start and end point are in the drawing area and, if not,
        # if there are intersections with the drawing-area-borders.
        # 1. To speed up, we have a vectorized Mapping.nofit() method which checks for each data
        # point if is is not in the drawing area and if so, encodes on which side(s) of the
        # drawing area it lies. Then, by checking if two consecutive data points are outside
        # of the drawing area on the same side (e.g. both points are on the left side of the
        # drawing area), we can omit the connection line because there is no chance of the line
        # crossing the drawing area borders. Furthermore, we only determine if the points are
        # in the drawing area once in this method here (it could be done once more in the
        # mapLine() or map() method but that's not our business here!)
        # 2. Furthermore, we check if two consecutive points which should be are mapped on the same
        # pixel. If so, we can skip one of that points and furthermore skip drawing that line. But
        # as it seems to me that drawing the same point twice yields no performance penalty (I guess
        # it just corresponds to setting a value in the underlying curses-array), we just draw every
        # point.
        for ds in self.seriesList:
            # First, determine where the data points lie outside of the drawing area
            outsides = self.mapping.nofit(ds.X, ds.Y)
            # 1. We can omit a line if two consecutive points share a nofit-direction
            # We only have to calculate this if we actually want to draw the lines
            if self.draw_lines:
                omitlines = outsides[0:-1] & outsides[1:]
                omitlines = numpy.append(omitlines, 15) # Hack so that the array sizes stay the same for iterating
            # 2. If two consecutive points are the same, omit the lines, too. To do so,
            # pre-calculate the mapping values.
            cols = numpy.empty(outsides.shape) # Pre initialize arrays for the mappings so that they have the
            rows = numpy.empty(outsides.shape) # same shape as the other array
            cols[outsides==0] = self.mapping.mapx(ds.X[outsides==0]) # Map the values
            rows[outsides==0] = self.mapping.mapy(ds.Y[outsides==0])
            cols = cols.astype(int) # Mapping.map() returns integer arrays but the types are changed when assigning
            rows = rows.astype(int) # to the bigger arrays. Ensure the types here again.
            # Try to draw the lines and draw the points
            for i in range(len(outsides)):
                # First try to draw the line if it is not obvious that it will not be drawn
                if self.draw_lines and not omitlines[i] and (rows[i], cols[i])!=(rows[i+1], cols[i+1]):
                    ax, ay, bx, by = ds.X[i], ds.Y[i], ds.X[i+1], ds.Y[i+1]
                    DEBUG(str(self.mapping))
                    DEBUG("{}, {}, {}, {}".format(ax, ay, bx, by))
                    for col, row in self.mapping.mapLine(ax, ay, bx, by):
                        self.window.addstr(row, col, "·", curses.color_pair(ds.color))
                # Then, draw the (current) point
                if not outsides[i]:
                    # The value is plottable, map it to a (px, py) plot location.
                    # col, row = self.mapping.map(ds.X[i],ds.Y[i])
                    # Plot the point at that location.
                    self.window.addstr(rows[i], cols[i], "+", curses.color_pair(ds.color))

        """
        DEPRECATED APPROACH
        # Plot the (straight) connection lines between the data points
        for ds in self.seriesList:
            for i in range(ds.length-1):
                ax, ay, bx, by = ds.X[i], ds.Y[i], ds.X[i+1], ds.Y[i+1]
                DEBUG(str(self.mapping))
                DEBUG("{}, {}, {}, {}".format(ax, ay, bx, by))
                for col, row in self.mapping.mapLine(ax, ay, bx, by):
                    self.window.addstr(row, col, "·", curses.color_pair(ds.color))
        # Plot the data points in front of the lines
        for ds in self.seriesList:
            DEBUG("NOTE ds.length %i" % ds.length)
            for i in range(ds.length):
                x, y = ds.X[i], ds.Y[i]
                # Check the value lies in the plottable area.
                if self.mapping.fits(x, y):
                    # The value is plottable, map it to a (px, py) plot location.
                    col, row = self.mapping.map(x,y)
                    # Plot the point at that location.
                    self.window.addstr(row, col, "+", curses.color_pair(ds.color))
        """

    def clearPlotArea(self):
        self.window.addstr(0, 0, " ")
        self.window.clrtobot()

    def clearData(self):
        self.seriesList = []

    def plot(self, X, Y, label="myData"):
        # Add the new data to the seriesList.
        self.seriesList.append(DataSeries(numpy.array(X), numpy.array(Y), label, color=self.colorList[len(self.seriesList)]))
        self.redraw()

    def redraw(self):
        # Determine the new size of the plotting area
        self.getPlotArea()
        # Clear the screen of any current plots.
        self.clearPlotArea()
        # Update axis limits
        self.updateAxis()
        # Update the mapping between x,y and row,col
        self.updateMapping()
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

class Figure(object):
    def __init__(self):
        self.seriesList = []

    def plot(self, x, y, label=""):
        self.seriesList.append(DataSeries(x, y, label))

    def show(self):
        curses.wrapper(lambda stdscr: self.drawingloop(stdscr))

    def drawingloop(self, stdscr):
        stdscr.clear()
        curses.curs_set(False)
        ax = Grapher(stdscr)
        for s in self.seriesList:
            ax.plot(s.X, s.Y, s.label)

        # DEBUG
        for i in range(0):
            ax.moveup()

        colornum = 0
        while True:
            k = stdscr.getkey()
            if k == 'q':
                break
            elif k == 'KEY_RESIZE':
                ax.redraw()
            elif k == 'r':
                ax.redraw()
            elif k == 'g':
                ax.toggleLegend()
            elif k == 't':
                ax.toggleTicks()
            elif k == 'c':
                ax.toggleLines()
            elif k == 'l':
                ax.moveright()
            elif k == 'h':
                ax.moveleft()
            elif k == 'j':
                ax.movedown()
            elif k == 'k':
                ax.moveup()
            elif k == 'w':
                ax.zoominy()
            elif k == 's':
                ax.zoomouty()
            elif k == 'a':
                ax.zoomoutx()
            elif k == 'd':
                ax.zoominx()
            elif k == 'x':
                ax.autosize()
            else:
                stdscr.addstr(0,0,k)

def plot(x, y, label=""):
    fig = Figure()
    fig.plot(x, y, label)
    fig.show()

if __name__ == '__main__':
    import numpy
    import math
    import time
    
    #m = Mapping(-3, 3, 0, 10, -3, 3, 0, 10)
    #m.mapLine(-5,-12, 1,2)

    # Determine example plots
    x = numpy.arange(-11.5, 13.5, .001)
    #x = numpy.array([0, .1]) # DEBUG
    #ya = [math.sin(i) for i in x]
    #yb = [(1/4)*math.sin(4*i) for i in x]
    #yc = [math.sin(i) + (1/4)*math.sin(4*i) for i in x]
    ya = numpy.sin(x)
    yb = 1/4 * numpy.sin(4*x)
    yc = numpy.sin(x) + 1/4*numpy.sin(4*x)
    yd = numpy.cos(x) + 1/4*numpy.cos(4*x)

    print("First, demonstrating a direct plot ...")
    time.sleep(1)
    plot(x, ya, "sin(x)")
    # exit() # DEBUG

    print("Now, demonstrating multiple plots in a Figure object.")
    time.sleep(1)
    f = Figure()
    f.plot(x, ya, "sin(x)")
    f.plot(x, yb, "(1/4)sin(4x)")
    f.plot(x, yc, "sin(x)+(1/4)sin(4x)")
    f.plot(x, yd, "cos(x)+1/4*cos(4*x)")
    f.show()
    print("And, Figure objects can be reused (shown again) after they have been closed.")
    time.sleep(1)
    f.show()

