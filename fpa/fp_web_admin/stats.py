# stats.py
# Michael Kirk 2015
#

import urllib
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
# from matplotlib.dates import DateFormatter

# not used?
# import datetime
# import StringIO
# import random

def htmlBoxplot(data):
#-------------------------------------------------------------------------------
# Parameter data should be an array of Datum, from a single traitInstance,
# of numerical type.
#
#
    fig=Figure()
    ax=fig.add_subplot(111)
    x=[]
    for datum in data:
        if not datum.isNA():
            x.append(float(datum.getValue()))
    ax.boxplot(x, vert=False)
    canvas=FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    png_output = png_output.getvalue().encode("base64")
    return '<img src="data:image/png;base64,{0}"/>'.format(urllib.quote(png_output.rstrip('\n')))
