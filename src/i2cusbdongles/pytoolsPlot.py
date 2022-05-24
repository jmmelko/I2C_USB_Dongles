#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
pytoolsPlot.py - to plot CSV-data (Comma Separated Values) from any source

Data are shown on either one of two Y-axis, depending on configuration.

Configuration of the plot is done in a configuration text file; the default
is 'pytoolsPlot.cfg'. Titles, labels, Y-axis limits, colors, linewidths,
markersizes, etc can be configured. Special treatment possible for Date or time
as x-axis. Window geometry (position, size) can also be set.

Scaling of the axis is possible formulas containing +, -, *, /, ** with any
float or int number, and functions like log, sqrt, sine, etc can be applied
(see configuration file for details).

CSV data come in a form like:
#Comment line - lines with first non-blanc character '#' are ignored
#ColA   ColB(Date&Time)      ColC,   ColD,   ColE, ...
    12, 2017-01-11 11:01:33, 17,     999.1,  0.1,  ...
    13, 2017-01-11 11:02:33, 20,     888.4,  1.7,  ...

Starting: to plot data in file 'CSVfile.log' run as:
pytoolsPlot path/to/CSVfile.log

As a convenience function, plotting very large files can be limited to the last
N values with the command line option -l N. To get help info run as:
pytoolsPlot -h

Download 'pytoolsPlot.py' from:  https://sourceforge.net/projects/i2cpytools/

N.B.: Program derived from GeigerLog: https://sourceforge.net/projects/geigerlog/
"""

import sys, os, time
import getopt                   # parse command line for options and commands

import matplotlib
try:
    matplotlib.use('Qt5Agg')        # MUST be done BEFORE importing pyplot!
except ValueError: 
    matplotlib.use('Qt4Agg') 
#matplotlib.use('TkAgg')        # an alternative to Qt4Agg, but ugly
import matplotlib.pyplot as plt # MUST import AFTER matplotlib.use()!
import matplotlib.dates  as mpld
import numpy             as np

__author__      = "ullix/jmmelko"
__copyright__   = "Copyright 2016-2022"
__credits__     = [""]
__license__     = "GPL"
__version__     = "1.0b"         # derived from GeigerLog plot

python_version  = sys.version.replace('\n', "")     # 3.5.2
mplVersion      = matplotlib.__version__            # 2.2.0
numpyVersion    = np.version.version                # 1.14.2

# CONSTANTS

# help info
# debug and verbose not yet in use
USAGE = """
Usage:  pytoolsPlot.py [Options] Datafile

Options:
    -h, --help          Show this help and exit
    -d, --debug         Run with printing debug info
                        Default is debug = False
    -v, --verbose       Be more verbose
                        Default is verbose = False
    -V, --Version       Show version status and exit
    -c, --config name   Set the configuration file to name;
                        name is the configuration file
                        including path.
                        Default is 'cfg/pytoolsPlot.cfg'
    -l, --last N        Plot only the last N records

Datafile                File must be of type CSV
                        (Comma Separated Values)
                        If data file is not in same
                        directory as program, a relatve
                        or absolute path must be given:
                        e.g.: path/to/csvfile4plotting
"""

CONFIGFILE      = "pytoolsPlot.cfg"
configfile      = CONFIGFILE
CONFIGINFO      = """
A default configuration will be used. However, you might want to dowload a
template and adapt it to your needs. Download template 'pytoolsPlot.cfg'
from: https://sourceforge.net/projects/i2cpytools/
"""

# DEFAULT CONFIGURATION
LABELS          = { "title":          "Title",
                    "xlabel":         "XLabel",
                    "ylabelleft":     "YLabelLeft",
                    "ylabelright":    "YLabelRight",
                  }

SETTINGS        = { "yscaleleft":     "none, none",
                    "yscaleright":    "none, none",
                    "window":         "0, 0, 1200, 750",
                    "markerscale":    "auto",
                    "missingvalue":   "nan",
                    "missingaction":  "ignore",
                  }

# for ordered printing of config
CFGSTRS         = ("title", "xlabel", "ylabelleft", "ylabelright", "yscaleleft",
                   "yscaleright", "window", "markerscale", "missingvalue",
                   "missingaction")

# colors used for lines and markers in plot
COLORS          = ("black", "red", "orange", "gold", "green", "blue", "cyan",
                   "magenta", "purple", "pink")

#colors for the terminal
# https://gist.github.com/vratiu/9780109
TCYAN           = '\033[96m'     # cyan
tPURPLE         = '\033[95m'     # purple (dark)
tBLUE           = '\033[94m'     # blue (dark)
TGREEN          = '\033[92m'     # light green
TYELLOW         = '\033[93m'     # yellow
TRED            = '\033[91m'     # red
TDEFAULT        = '\033[0m'      # default, i.e greyish
BOLD            = '\033[1m'      # white (bright default)
UNDERLINE       = '\033[4m'      # underline
BOLDREDUL       = '\033[31;1;4m' # bold, red, underline
BOLDRED         = '\033[31;1m'   # bold, red - but is same color as TRED

NORMALCOLOR     = TGREEN         # normal printout
ERRORCOLOR      = TYELLOW        # error message

# Variables
debug           = False
verbose         = False
plotLastValues  = None

##############################################################################

def version_status():
    """returns versions as list"""

    version_status = []
    version_status.append([u"pytoolsPlot.py",  "{}".format(__version__)])
    version_status.append([u"Python",          "{}".format(python_version)])
    version_status.append([u"matplotlib",      "{}".format(mplVersion)])
    version_status.append([u"numpy",           "{}".format(np.version.version)])

    return version_status


def datestr2num(string_date):
    """convert a Date&Time string to a matplotlib timestamp"""

    # Date&Time strings are attempted to be recognized; it is unclear, how the
    # parser works, but most formats should be caught. Details here:
    # https://github.com/matplotlib/matplotlib/blob/master/lib/matplotlib/dates.py

    py3string_date = string_date.strip().decode("ASCII") # required by Py3
    dt = mpld.datestr2num(py3string_date)

    return dt


def bell():
    """Wring the bell once"""

    print("\7")


def cprint(*args, end = "\n", color = NORMALCOLOR):
    """color print the args"""

    print(color, end="")
    for arg in args:    print(arg, end=" ")
    print(TDEFAULT, end=end)


def ecprint(*args, end = "\n", color = ERRORCOLOR):
    """error color print the args"""

    cprint(*args, end = "\n", color = color)


def exceptPrint(e, excinfo, srcinfo):
    """Print details (errmessage, file, line no) on an exception"""

    exc_type, exc_obj, exc_tb = excinfo
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print()
    ecprint("ERROR: '{}' in file: '{}' in line {}".format(e, fname, exc_tb.tb_lineno))
    ecprint(srcinfo)


def handle_close(event):
    # window responds to CTRL-W, i.e not to a SIGNAL
    # but program can be closed by SIGINT from calling program

    bell()
    cprint("pytoolsPlot is closed")
    #cprint('event:', event, color=TRED)


def plotData(datafile, coldata, rowmax, colmax, xcol, cfg):

    # make figure
    fig, ax1 = plt.subplots(figsize=(16,10), dpi=70, facecolor="none")

    # define events and handlers
    fig.canvas.mpl_connect('close_event', handle_close)# closes with CTRL-W

    # position figure on screen
    fm  = plt.get_current_fig_manager()
    #print ("current figmanager=", fm)    # matplotlib.backends.backend_qt5.FigureManagerQT
    #print(matplotlib.get_backend())      # e.g. "Qt4Agg" or "TkAgg"
    #print(matplotlib.matplotlib_fname()) # location of matplotlibrc, e.g.
    #/usr/local/lib/python3.5/dist-packages/matplotlib/mpl-data/matplotlibrc

    # set Window Title
    fm.set_window_title("Data from: {} ({} records)".format(datafile, rowmax))


    windowgeom = cfg["window"]
    #print("windowgeom:", windowgeom)
    xpos   = int(windowgeom[0])
    ypos   = int(windowgeom[1])
    width  = int(windowgeom[2])
    height = int(windowgeom[3])
    if matplotlib.get_backend()== "Qt4Agg":
        fm.window.setGeometry(xpos, ypos, width, height)
    elif matplotlib.get_backend()== "TkAgg":
        # The format is: widthxheight+x+y'', where width and height are positive
        # integers, x and y may be positive and negative integers.
        # slight ypos difference; maybe TkAgg is not including panel size?
        fm.window.wm_geometry("{}x{}+{}+{}".format(width, height, xpos, ypos))
        #print("{}x{}+{}+{}".format(width, height, xpos, ypos))

    # adjust layout
    right = 0.8 # needed for legend position
    fig.subplots_adjust(hspace=None, wspace=None , left=.065, top=0.93, bottom=0.060, right=right)

    # add title
    fig.suptitle(cfg['title'][0], fontsize=16, fontweight='bold')

    # make 2nd Y-axis
    ax2 = ax1.twinx()

    # add labels to X and Yleft and Yright axis
    ax1.set_xlabel(cfg['xlabel'][0],      fontsize=14, fontweight='bold')
    ax1.set_ylabel(cfg['ylabelleft'][0],  fontsize=14, fontweight='bold')
    ax2.set_ylabel(cfg['ylabelright'][0], fontsize=14, fontweight='bold')

    # add grid
    ax1.grid(True, which="major")                # major grid, solid
    ax1.grid(True, which="minor", linestyle=':') # minor grid, dotted
    ax1.minorticks_on()
    ax1.tick_params(labelsize=14, which="both")
    ax1.tick_params(which='major', length=6, width=1)

    #ax2.grid(True, which="both") # works, but makes chaos: grids not synchronized
    ax2.minorticks_on()
    ax2.tick_params(labelsize=14, which="both")
    ax2.tick_params(which='major', length=6, width=1)

    # set Y-axis limits if defined; both low and high must be defined
    yl = cfg["yscaleleft"]
    if yl[0].upper() != "NONE" and yl[1].upper() != "NONE":
        try:
            ax1.set_ylim(float(yl[0]), float(yl[1]))
        except:
            ecprint("ERROR: Y-axisLeft could not be scaled:", yl)

    yr = cfg["yscaleright"]
    if yr[0].upper() != "NONE" and yr[1].upper() != "NONE":
        try:
            ax2.set_ylim(float(yr[0]), float(yr[1]))
        except:
            ecprint("ERROR: Y-axisRight could not be scaled:", yr)

    if cfg['markerscale'][0].upper() == "AUTO":
        mksfactor = 10 / np.log10(rowmax) # big markers for few points, small for many
    else:
        mksfactor = 1

    # add plots
    ax1.plot([], [], ' ', label="Left Y-axis")  # Dummy for legend title
    ax2.plot([], [], ' ', label="Right Y-axis") # dito
    xcoldata = coldata[xcol]
    for i in range(1, colmax):
        icfg   = cfg[i]
        icfg0u = icfg[0].upper()
        #print("icfg0u:", icfg0u)
        if "YL" in icfg0u or  "YR" in icfg0u:
            ycoldata = coldata[i]

            lbl = icfg[3][0:10] # limit label to 10 chars
            clr = icfg[4]
            lwi = icfg[5]
            mks = float(icfg[6]) * mksfactor

            if "YL" in icfg0u:
                if xcol > 0 and "DATE" in cfg[xcol][0].upper() :
                    ax1.plot_date(xcoldata, ycoldata, color=clr, linewidth=lwi, linestyle='solid', label=lbl, fmt="o", markeredgecolor=clr,  markersize=mks)
                else:
                    ax1.plot     (xcoldata, ycoldata, color=clr, linewidth=lwi, linestyle='solid', label=lbl, fmt="o", markeredgecolor=clr,  markersize=mks)

            elif "YR" in icfg0u:
                if xcol > 0 and "DATE" in cfg[xcol][0].upper() :
                    ax2.plot_date(xcoldata, ycoldata, color=clr, linewidth=lwi, linestyle='solid', label=lbl, fmt="o", markeredgecolor=clr,  markersize=mks)
                else:
                    ax2.plot     (xcoldata, ycoldata, color=clr, linewidth=lwi, linestyle='solid', label=lbl, fmt="o", markeredgecolor=clr,  markersize=mks)


    # add the legend (unfortunately, results in 2 separate legends
    ax1.legend(bbox_to_anchor=(1/right, 1.0), loc='upper right', borderaxespad=0., fontsize=14)
    ax2.legend(bbox_to_anchor=(1/right, .50), loc='upper right', borderaxespad=0., fontsize=14)


def getData(datafile, xcol, timecol, cfg):
    """get the CSV file and extract the gendata"""

    datafile = os.path.normpath(datafile)

    cprint("\nData from file '{}' : ".format(datafile))

    # verify file existence
    if not (os.path.isfile(datafile)):
        ecprint("ERROR: File not found!")
        return 1, None, None, None

    # verify readability
    if not os.access(datafile, os.R_OK):
        ecprint("ERROR: File is not readable!")
        return 1, None, None, None

    with open(datafile, "rt") as cfghandle:
        llines = cfghandle.readlines()      # llines is list of lines

    # numpy.genfromtxt fails with less than 2 records; make sure you have more
    # exclude comment lines
    lines = 0
    for a in llines:
        astr = a.strip()
        if len(astr) > 0 and astr[0] != "#": lines += 1
        if lines > 2: break
    if lines < 2:
        ecprint("\nFound total of {} records -- need minimum of 2 for plotting".format(lines))
        return 1, None, None, None

    lll = len(llines)
    for i in range(min(4, lll)):
        cprint("Line {:<6d} : ".format(i+1), llines[i][:-1])
    if len(llines) > 3:
        cprint("     ...")
        cprint("Line {:<6d} : ".format(lll-2), llines[lll-3][:-1])
        cprint("Line {:<6d} : ".format(lll-1), llines[lll-2][:-1])
        cprint("Line {:<6d} : ".format(lll),   llines[lll-1][:-1])

    cprint("\nFound total of {:,} lines (including comments)".format(lll))

    # get the data using numpy
    # -- on numpy < 1.14 must use 'file', like:
    #    gendata    = np.genfromtxt(datafile, delimiter=",", converters = {1: old_datestr2num})
    # -- on numpy >=1.14 can use 'list' of lines
    mval   = cfg["missingvalue"][0]
    plvals = 0 if plotLastValues == None else max(plotLastValues, 2)
    if timecol == False:
        gendata    = np.genfromtxt(llines[-plvals:], delimiter=",", missing_values=mval, filling_values=np.nan, usemask=True, autostrip=True)
    else:
        gendata    = np.genfromtxt(llines[-plvals:], delimiter=",", converters = {xcol - 1: datestr2num}, missing_values=mval, filling_values=np.nan, usemask=True, autostrip=True)

    # gendata is 'masked array', with True indicating an element with 'missing value'.
    # Apply mask with '.filled(np.nan)'
    gendata = gendata.filled(np.nan)
    #for i in range(0, 3): cprint("gendata[{}]:".format(i), gendata[i])
    colmax = np.shape(gendata)[1]
    rowmax = np.shape(gendata)[0]
    cprint("Found total of {} data records in {} data columns (Col0 is index):".format(rowmax, colmax))

    # make individual vars to hold the column data
    coldata     = np.empty((1 + np.shape(gendata)[1],np.shape(gendata)[0]))
    coldata[0]  = np.arange(rowmax)     # extra col as index
    for i in range(0, colmax):   coldata [i + 1] = gendata[:,i]

    return 0, coldata, colmax +1, rowmax


def printData(coldata, colmax, rowmax, header=False, cfg=None, timecol=None, xcol=None):
    """
    print first and last rows of data, as well as Mean, Min, Max, ignoring 'nan'
    values. A header may be applied after configuration
    """

    if header:

        # Header: X or time
        cprint("X-axis      :", end=" ")
        for i in range(0, colmax):
            a = "---"
            if xcol == i:
                if timecol:
                    a = 'Date/Time'
                else:
                    a = "X"
            cprint("{:>10s}".format(a), end=" ")
        cprint()

        # Header: Label
        cprint("Label       :", end=" ")
        for i in range(0, colmax):
            try:
                a = cfg[i][3]
            except:
                a = "---"
            cprint("{:>10s}".format(a[:10]), end=" ")
        cprint()

        # Header: Scaling
        cprint("Scaling     :", end=" ")
        for i in range(0, colmax):
            try:
                a = cfg[i][1]
            except:
                a = "---"
            cprint("{:>10s}".format(a[:10]), end=" ")
        cprint()

    # print col numbering, col1, col2, col3, ...
    dformat = "{:12.4f}"
    dcol    = "Column ID   :"
    for i in range(0, colmax): dcol += "{:>12s}".format("Col"+str(i))
    cprint(dcol)

    # print first and last few rows of data
    if rowmax >= 3:
        lrange = (0, 1, 2, rowmax - 3, rowmax - 2, rowmax - 1)
    elif rowmax == 2:
        lrange = (0, 1)
    else:
        lrange = (0)
    for j in lrange:
        ddata = "data[{:6d}]:".format(j)
        for i in range(0, colmax): ddata += dformat.format(coldata[i][j])
        cprint(ddata)
        if j == 2 : cprint("...")

    # print mean, min, max, including for X-axis
    #np.seterr(all="ignore") # floating point errors (works here too for text fields
    np.warnings.filterwarnings('ignore')    # warnings result from text fields
    dmean   = "Mean        :"
    dmin    = "Min         :"
    dmax    = "Max         :"
    for i in range(0, colmax):
        # np.nan... ignores 'nan' values
        dmean += dformat.format(np.nanmean(coldata[i]))
        dmin  += dformat.format(np.nanmin (coldata[i]))
        dmax  += dformat.format(np.nanmax (coldata[i]))
    cprint()
    cprint(dmin)
    cprint(dmean)
    cprint(dmax)
    np.warnings.filterwarnings("default")


def getRawConfig(configfile):
    """
    Load configuration and do first checks.
    Return errorflag, cfg, timecol and xcol
    """

    cprint("Config file:", configfile)
    cfg     = {}        # empty config
    xcol    = 0         # default X-axis is the index col = col 0
    timecol = False     # by default there is not time column

    if not os.path.isfile(configfile):              # file not existing
        ecprint("ERROR: Configuration file not found!")
        ecprint(CONFIGINFO)
        # as the file is not found, a default will be
        # used and its syntax will be ok

    elif not os.access(configfile, os.R_OK):        # file not readable
        ecprint("ERROR: Config file exists, but is not readable")
        return 1, cfg, timecol, xcol

    else:                                           # read the file as lines
        with open(configfile, "rt") as cfghandle:
            for line in cfghandle:
                a = line.strip()

                if a == "" or a[0] == "#":
                    pass
                else:
                    #print("a=line:", a)
                    if ":" in a:
                        ak, av              = a.split(":", maxsplit=1)
                        aks                 = ak.strip()
                        avs                 = av.strip()
                        if aks.isdigit():   # dict key is number
                            key             = int(aks)
                            if key == 0: continue    # ignore index zero
                            avss            = avs.split(',')
                            cfg [key]       = avss

                            if avss[0].upper().startswith("TIME"): # found time
                                timecol = True
                                xcol    = key
                            elif avss[0].upper().startswith("DATE"): # found Date
                                timecol = True
                                xcol    = key
                            elif avss[0].upper().startswith("X"):  # found X
                                timecol = False
                                xcol    = key

                        else:               # dict key is string
                            key             = aks
                            if key in LABELS:
                                avs         = avs.replace(',', ' ') # no comma in labels
                            avss            = avs.split(',')
                            cfg [key]       = avss
                    else:
                        ecprint("ERROR in Config file: ':' is missing in line: ", a)
                        return 1, cfg

    # add any missing labels to cfg
    for a in LABELS:
        if a not in cfg:  cfg[a] = LABELS[a].split(",")

    # add any missing settings to cfg
    for a in SETTINGS:
        if a not in cfg:  cfg[a] = SETTINGS[a].split(",")

    # print the raw configuration
    #print("\nRaw configuration:")
    #for key, value in cfg.items():
    #    print ("{} : {}".format(key, value))

    return 0, cfg, timecol, xcol


def getFinalConfig(cfg, colmax):
    """read the configuration file and clean up"""

    if colmax < 1:
        ecprint("ERROR: Must have at least 1 data column for a plot versus index")
        return 1, cfg

    # add any missing columns
    yaxis  = ("yl", "yr")
    for i in range(1, colmax):
        if i not in cfg:
            #             purpose, scale,  ref,  name,    color,        linewidth, Markersize
            cfgstr      =     "{},  none,  none, Value{},    {},        {},           {}"
            cfg[i] = cfgstr.format(yaxis[(i - 1) % 2], i, COLORS[(i - 1) % 10], 2, 2).split(",")

    # clean up: strip all strings
    for a in cfg:
        for i in range(len(cfg[a])):
            cfg[a][i] = cfg[a][i].strip()

    # make sure to have at least one Y-axis; exit if not
    y = 0
    for a in cfg:
        #print("a:", a, cfg[a])
        if isinstance(a, int):
            if cfg[a][0].upper().startswith("Y"):
                y += 1
                break
    if y == 0:
        ecprint("ERROR: No Y-axis defined")
        return 1, cfg

    # print the final configuration
    cprint("\nFinal configuration after cleaning:")
    for a in CFGSTRS:
        cprint ("{:<14s} : {}".format(a, cfg[a]))
    for i in range(1, colmax):
        cprint ("{:<14d} : {}".format(i, cfg[i]))

    return 0, cfg


def scaleData(data, scale):
    """
    apply the calculations declared in config
    Return: Success (True|False) and the modified data
    NOTE: scale is in upper-case, but may be empty or NONE
    """

    if scale == "" or scale == "NONE": return True, data

    #cprint("scaleData: IN : scale: '{:30s}', data IN : {}".format(scale, data[:5]))

    # example: scale: LOG(COL)+1000
    # becomes:        log(data)+1000
    ls = scale
    ls = ls.replace("COL",    "data")         # the data of that column
    ls = ls.replace("LOG",    "np.log")       # Log to base e; natural log
    ls = ls.replace("LOG10",  "np.log10")     # Log to base 10
    ls = ls.replace("LOG2",   "np.log2")      # Log to base 2
    ls = ls.replace("SIN",    "np.sin")       # sine
    ls = ls.replace("COS",    "np.cos")       # cosine
    ls = ls.replace("TAN",    "np.tan")       # tangent
    ls = ls.replace("SQRT",   "np.sqrt")      # square root
    ls = ls.replace("CBRT",   "np.cbrt")      # cube root
    ls = ls.replace("ABS",    "np.absolute")  # absolute value

    try:
        a = eval(ls)
    except Exception as e:
        ecprint("ERROR interpreting formula: '{}', errmsg: {}".format(scale, e))
        return False, data

    # print first 3 datapoints of IN and OUT
    #print("scaleData: scale: '{:30s}', data IN: {}, data OUT: {}".format(ls, data[:3], a[:3]))

    return True, a


def applyConfigToData(cfg, data, colmax):

    for i in range(1, colmax):
        purpose = cfg[i][0].upper()
        if purpose.startswith("IG"):   continue  # ignore column
        if purpose.startswith("DATE"): continue  # no adjustments for Date
        scale   = cfg[i][1].upper()
        ref     = cfg[i][2].upper()
        gendata = data[i]
        if ref == "REL":  gendata = gendata - gendata[0]
        success, gendata =  scaleData(gendata, scale)
        if success:
            data[i] = gendata
        else:
            ecprint("ERROR in Configuration: Axis definition;", cfg[i])
            return 1, None

    return 0, data


def main(datafile, configfile = CONFIGFILE):

    cprint("\npytoolsPlot -------------------- PLOTTING CSV DATA" + "-"*50)

    # Get the raw configuration, with timecol, Xcol
    cprint("\nGet raw configuration from", end="")
    flag, cfg, timecol, xcol = getRawConfig(configfile = configfile)
    if flag: return flag
    cprint("X-axis:   ", end="")
    if xcol == 0:
        cprint("None configured; default will be index column 0")
    else:
        if timecol == False:
            cprint("will be column {} as a non-'time' axis".format(xcol))
        else:
            cprint("will be column {} as a 'Date' or 'time' axis".format(xcol))

    # get the datafile and extract the data
    flag, coldata, colmax, rowmax = getData(datafile, xcol, timecol, cfg)
    if flag: return flag

    # now that colmax is known get final config
    flag, cfg = getFinalConfig(cfg, colmax)
    if flag: return flag

    # print data before configuration and scaling
    cprint("Data BEFORE applying configuration and scaling:")
    printData(coldata, colmax, rowmax)

    # calculations involving more than 1 column; not yet configurable
    #coldata[6] = coldata[3] - coldata[6] # Temp -Traw
    #coldata[9] = coldata[3] - coldata[9] # Temp -T_LM75
    #coldata[3] = coldata[9] - coldata[3] # T_LM75 - Temp

    # apply config and scaling
    flag, newdata = applyConfigToData(cfg, coldata, colmax)
    if flag: return flag

    # print data after configuration and scaling
    cprint("\nData AFTER applying configuration and scaling:")
    printData(newdata, colmax, rowmax, header = True, cfg = cfg, timecol = timecol, xcol = xcol)

    # plot the data
    plotData(datafile, coldata, rowmax, colmax, xcol, cfg)

    # show plot
    plt.show(block=True)        # shows until window closed
    #plt.show(block=False)      # effectively not showing

    return 0


###############################################################################
if __name__ == "__main__":

    # parse command line options; sys.argv[0] is progname
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdvVc:l:",
                    ["help", "debug", "verbose", "Version", "config", "last"])
    except getopt.GetoptError as errmessage :
        # print info like "option -a not recognized", then exit
        ecprint("ERROR: '{}', use './pytoolsPlot -h' for help".format(errmessage) )
        sys.exit(1)

    # processing the options
    for opt, optval in opts:

        if opt in ("-h", "--help"):
            print(USAGE)
            sys.exit(0)

        elif opt in ("-d", "--debug"):
            debug = True    # not yet implemented

        elif opt in ("-v", "--verbose"):
            verbose = True    # not yet implemented

        elif opt in ("-V", "--Version"):
            print ("Version status:")
            for a in version_status():
                print( "   {:15s}: {}".format(a[0], a[1]))
            sys.exit(0)

        elif opt in ("-c", "--config"):
            cf = optval.strip()
            if os.path.isfile(cf):
                if os.access(cf, os.R_OK):
                    configfile = cf
                else:
                    ecprint("ERROR: configuration file '{}' not readable".format(cf))
                    sys.exit()
            else:
                ecprint("ERROR: configuration file '{}' not found".format(cf))
                sys.exit()

        elif opt in ("-l", "--last"):
            try:
                plotLastValues = int(float(optval))
            except Exception as e:
                ecprint("ERROR in command options: '{}' must be convertible to an integer number".format(optval))
                sys.exit()


    # processing the args
    # so far the only arg is the Datafile
    # if multiple arg given, only the last is used as Datafile
    arg = ""
    for arg in args:
        pass
        #print("arg:", len(arg), arg)

    try:
        if len(arg) > 0:
            main(arg, configfile = configfile)
        else:
            ecprint("ERROR: No Datafile defined!", USAGE)
    except Exception as e:
        exceptPrint(e, sys.exc_info(), "ERROR plotting the data")
        ecprint(USAGE)

