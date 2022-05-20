#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import time, os, sys, subprocess, signal

from i2cusbdongles import glob

if glob.PLATFORM != 'win32':
    import curses
else:
    import keyboard                       # not available on Windows

def writeToFile(filename, text):
    """ Write the log file """

    glob.logfile = open(os.path.normpath(filename), "a", buffering = 1)
    glob.logfile.write(text + "\n")
    glob.logfile.close()
    glob.logfile = None


def curses_checker(stdscr):
    """checking for keypress; uses curses, not available on windows"""

    stdscr.nodelay(True)            # do not wait for input when calling getch
    #curses.noecho()
    #curses.cbreak()

    rv = ""
    while True:                     # collect all last keypresses
        c = stdscr.getch()
        if c == -1:                 return rv
        elif c >= 32 and c <= 128:  rv += ", " + chr(c)

def keyboard_checker(events):
    
    rv = ""
    for e in events: 
        rv += ", " + e.name
    return rv
        

def checkForKeys():
    """checking for a key press; uses curses, not available on windows"""
    
    try:
        return curses.wrapper(curses_kchecker)
    except NameError:
        try:
            if not keyboard._recording:
                keyboard.start_recording()
                return ""
            else:
                try:
                    events = keyboard.stop_recording()
                    return keyboard_checker(events)
                except (ValueError,KeyError):                   
                    keyboard._recording = None # to handle a bug in the keyboard module
                    return ""
        except NameError:
            return ""


def version_status():
    """returns versions as list"""

    version_status = []
    version_status.append([u"I2Cpytools",      "{}".format(glob.__version__)])
    version_status.append([u"Python",          "{}".format(glob.python_version)])

    return version_status


def clamp(n, minn, maxn):
    """limit return value to be within minn and maxn"""

    return min(max(n, minn), maxn)


def getProgName():
    """Return program base name, i.e. 'geigerlog' even if it was named
    'geigerlog.py' """

    progname          = os.path.basename(sys.argv[0])
    progname_base     = os.path.splitext(progname)[0]

    return progname_base


def getProgPath():
    """Return full path of the program directory; ends WITHOUT '/' """

    dp = os.path.dirname(os.path.realpath(__file__))
    return dp

def getPackagePath():
    
    dp = os.path.normpath(os.path.join(getProgPath(), '../../'))
    return dp   

def getDataPath():
    """Return full path of the data directory; ends WITHOUT '/' """

    dp = os.path.normpath(os.path.join(getPackagePath(), glob.dataDirectory))
    return dp


def strtime():
    """Return current time as YYYY-MM-DD HH_MM_SS"""

    return time.strftime("%Y-%m-%d %H_%M_%S")


def ncprint(*args, color = glob.HILITECOLOR, end = "\n"):
    """Normal color print """

    print(color, end='')
    print(*args, end='')
    print(glob.NORMALCOLOR, end=end)


def ecprint(*args, color = glob.ERRORCOLOR, end="\n"):
    """Error color print """

    ncprint(*args, color = color, end=end)


def fncprint(*args, color = glob.HILITECOLOR, end = "\n"):
    """formatted normal color print; begins printing in col 59"""

    print(color, " " * 58, *args, end='')
    print(glob.NORMALCOLOR, end=end)


def fecprint(*args, color = glob.ERRORCOLOR, end="\n"):
    """formatted error color print """

    fncprint(*args, color = color, end=end)


def bell():
    """Wring the bell"""

    print("\7")


def infoPrint(dongle, dongle_name):
    """prints dongle use status and any connected sensors/modules"""

    if dongle != None:
        ncprint("   {:25s} : {}".format("Dongle in use", dongle))
        ncprint("   {:25s} :     {}".format("   connected with", dongle.name))
    else:
        ncprint("   {:25s} : {}".format("Dongle NOT in use", dongle))


def exceptPrint(e, excinfo, srcinfo):
    """Print exception details (errmessage, file, line no)"""

    exc_type, exc_obj, exc_tb = excinfo
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print()
    if glob.debug:
        raise e
    else:
        ecprint("ERROR: '{}' in file: '{}' in line {}".format(e, fname, exc_tb.tb_lineno))
        ecprint(srcinfo)


def shutdown():
    """ Closes sensors and dongles """

    for sensor in glob.sensors:        
        if sensor['hndl'] is not None:            
            try:
                print("Closing sensor %s" % sensor['name'])
                sensor['hndl'].close()
                print('Sensor successfully closed')
            except AttributeError:
                pass

    for dongle in glob.dongles.values():
        
        if dongle != None:
            dongle.close()

    if glob.logfile != None:
        glob.logfile.close()
        print("Logfile is closed")

    if glob.subxpid != None:
        #os.kill(glob.subxpid, signal.SIGUSR1) # closes only when Windows has focus
        try:
            os.kill(glob.subxpid, signal.SIGINT)   # closes always (but CTRL-C on
                                               # the window does NOT work
            print("Plot is closed")
        except PermissionError:
            print("Could not close plot")
    print()


def signal_handler(signal, frame):
    """Allows to handle the signals SIGINT, SIGTSTP, SIGQUIT, SIGUSR1, SIGUSR2.
    Requires these commands in main:
    signal.signal(signal.SIGINT,  util.signal_handler)   # to handle CTRL-C
    signal.signal(signal.SIGTSTP, util.signal_handler)   # to handle CTRL-Z
    signal.signal(signal.SIGQUIT, util.signal_handler)   # to handle CTRL-\
    signal.signal(signal.SIGUSR1, util.signal_handler)   # to handle user signal1
    signal.signal(signal.SIGUSR2, util.signal_handler)   # to handle user signal2
    """

    print()
    #print("signal_handler: Signal:", signal, "frame:", frame)

    if signal == 2:         # SIGINT CTRL-C
        # shutdown

        print('CTRL-C Keyboard Interrupt - Exiting')
        shutdown()


    elif signal == 3:        # SIGQUIT  CTRL-\
        # show graph from logfile (if logfile already defined)

        #plotGraph(glob.logfilename)
        # zero: no graph updates
        # -N  : N>0: one last update, then no more
        #  N  : N>0: update every N seconds, but not faster than cycletime
        try:
            si = float(input("Current graphcycle: {} sec. Enter new graphcycle (0 ... 60) sec: ".format(glob.graphcycle)))
            if si < 0: plotGraph(glob.logfilename)
            glob.graphcycle = max(min(si, 60),0)
            print("New graphcycle:", glob.graphcycle)
        except:
            print("Unchanged graphcycle:", glob.graphcycle)

        return


    elif signal == 20:     # SIGTSTP CTRL-Z
        # show and modify cycletime

        try:
            si = float(input("Current cycletime: {} sec. Enter new cycletime (0 ... 60) sec: ".format(glob.cycletime)))
            glob.cycletime = max(min(si, 60),0)
            print("New cycletime:", glob.cycletime)
        except:
            print("Unchanged cycletime:", glob.cycletime)

        return


    # SIGUSR1 and SIGUSR2 are user-defined signals; they aren't triggered
    # by any particular CTRL-<key> action
    # use os.kill(os.getpid(), signal.SIGUSR1) to send signal to prog with PID
    elif signal == 10:     # SIGURS1
        print("util.signal_handler got signal 10 = SIGURS1")


    elif signal == 12:     # SIGURS2
        print("util.signal_handler got signal 12 = SIGURS2")


    else:
        print("util.signal_handler got unknown signal:", signal, frame) # unknown signal

    sys.exit(0)


def plotGraph(logfilename):
    """ Calls the pytoolsPlot program to plot the graph """

    if glob.subxpid != None:
        #os.kill(glob.subxpid, signal.SIGUSR1) # closes only when Windows has focus
        try:
            os.kill(glob.subxpid, signal.SIGINT)   # closes always (but CTRL-C on
                                               # the window does NOT work
        except PermissionError:
            pass                         
                                    
    if not os.access(logfilename, os.R_OK):
        print("Logfile not found \7")
        return

    args = []
    if glob.PLATFORM.lower() == 'win32':
        args.append(str(sys.executable))
    args.append(os.path.join(getProgPath(),'pytoolsPlot.py'))
    args.append("-c")
    args.append(os.path.join(getPackagePath(),glob.configfile))
    if glob.plotLastValues != None:
        args.append("-l")
        args.append(str(glob.plotLastValues))
    args.append(os.path.join(getDataPath(),logfilename))
    if glob.subx != None:
        glob.subx.terminate
        glob.subx.kill

    print(args)

    try:
        #print("args:", args)
        subx         = subprocess.Popen(args)
        glob.subx    = subx
        glob.subxpid = subx.pid
        #subx.wait(1)
        #print("\7subx:", subx, subx.pid, subx.returncode)
        #subx.terminate
        #subx.kill ()

    except Exception as e:
        bell()
        print("ERROR from subprocess in util: ", e)



#def askDongle(dongle, addr, data, rbytes, wait_time=0, name="no name", info="no info", doPrint=True, end="\n"):
#    """Redirect Write and Read to/from dongle to the correct dongle"""
#
#    if dongle == 'ELVdongle':   # ELV
#        answ = glob.dongles['ELVdongle'].ELVaskDongle(addr, data, rbytes, wait_time=wait_time, name=name , info=info, doPrint=doPrint, end=end)
#
#    elif dongle == 'ISSdongle':   # ISS
#        answ = glob.dongles['ISSdongle'].ISSaskDongle(addr, data, rbytes, wait_time=wait_time, name=name , info=info, doPrint=doPrint, end=end)
#
#    elif dongle == 'IOW-DG': # IOW
#        answ = glob.dongles['IOW-DG'].IOWaskDongle(addr, data, rbytes, wait_time=wait_time, name=name , info=info, doPrint=doPrint, end=end)
#
#    else:
#        print("Dongle '{}' is undefined".format(dongle))
#        sys.exit()
#
#    return answ

