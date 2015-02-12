# stats.py
# Michael Kirk 2015
#
# NB Environment var MPLCONFIGDIR must be set before importing this module.
# It gives a folder for matplotlib stuff, must be writeable by web server.
#

import urllib
import StringIO
import flask

import os
#os.environ['MPLCONFIGDIR'] = '***REMOVED***/matplotlib/'
#os.environ['MPLCONFIGDIR'] = flask.current_app.config['MPLCONFIGDIR']
#import os
#import tempfile
#os.environ['MPLCONFIGDIR'] = tempfile.mkdtemp()
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure


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
