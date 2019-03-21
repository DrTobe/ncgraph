# NCGraph
Python NCurses Grapher Class (terminal plotting library).

## Usage

1. Direct plotting: `ncgraph.plot(x, y [,legend])`.
2. Create a figure object with `ncgraph.Figure()`, add plots with `figure.plot(x,y)` and show the figure object with `figure.show()`.

While the curses application is running, the keys are (currently hardcoded) mapped as follows:
* 'q': quit
* 'g': toggle legend
* 't': toggle x-ticks and y-ticks (bottom and left border)
* 'h', 'j', 'k', 'l': vim-like keybindings for moving the drawing area
* 'w', 'a', 's', 'd': zoom the drawing area
* 'x': reset original view (fit all plots in the drawing area)

``` Python
import numpy
import math
import ncgraph

# Create example plotting data
x = numpy.arange(-3.5, 13.5, .01)
ya = numpy.sin(x)
yb = 1/4*numpy.sin(4*x)
yc = numpy.sin(x) + 1/4*numpy.sin(4*x)
yd = numpy.cos(x) + 1/4*numpy.cos(4*x)

# Direct plotting
ncgraph.plot(x, ya, "sin(x)")

# Multiple plots in a Figure object
fig = ncgraph.Figure()
fig.plot(x, ya, "sin(x)")
fig.plot(x, yb, "(1/4)sin(4x)")
fig.plot(x, yc, "sin(x)+(1/4)sin(4x)")
fig.plot(x, yd, "cos(x)+(1/4)cos(4x)")
fig.show()

# After closing, the Figure object can be shown again
fig.show()
```

![Example Output](screens/example-main.png)
