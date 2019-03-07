# NCGraph
Python NCurses Grapher Class (terminal plotting library).

## Usage

The `ncgraph` plotting library has a very simple usage. Either, use `ncgraph.plot(x, y [,legend])` to plot a single function or create a figure object with `ncgraph.Figure()` while adding plots with `figure.plot(x,y)`. Finally, the figure object can be shown with `figure.show()`.

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
ya = [math.sin(i) for i in x]
yb = [(1/4)*math.sin(4*i) for i in x]
yc = [math.sin(i) + (1/4)*math.sin(4*i) for i in x]

# Direct plotting
ncgraph.plot(x, ya, "sin(x)")

# Multiple plots in a Figure object
fig = ncgraph.Figure()
fig.plot(x, ya, "sin(x)")
fig.plot(x, yb, "(1/4)sin(4x)")
fig.plot(x, yc, "sin(x)+(1/4)sin(4x)")
fig.show()

# After closing, the Figure object can be shown again
fig.show()
```

![Example Output](screens/example-main.png)
