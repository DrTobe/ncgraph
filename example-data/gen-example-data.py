import math
import numpy as np
from os import system

filename = "ex-sin-deg-360.csv"
system("touch %s" % filename)
with open(filename, 'w') as csv:
    for x in np.arange(0, 360, 0.25):
        y = math.sin((x/180) * math.pi)
        csv.write("%f, %f\n" % (x, y))
print("GEN %s" % filename)

filename = "ex-cos-deg-360.csv"
system("touch %s" % filename)
with open(filename, 'w') as csv:
    for x in np.arange(0, 360, 0.25):
        y = math.cos((x/180) * math.pi)
        csv.write("%f, %f\n" % (x, y))
print("GEN %s" % filename)
