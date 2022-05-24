#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
i2cusbdongles - software for the use of I2C sensors at a PC. It uses Python3 scripts.

The connection of the sensors to the PC is done via USB-dongles. This
release supports three different ones, which can be run simultaneously:

* ELV : ELV USB-I2C from ELV Elektronik AG ( https://www.elv.de/ )
* IOW : IO-Warrior24/28 Dongle (IOW-DG) from Code Mercenaries (https://www.codemercs.com/de )
* ISS : USB-ISS from Devantech ( https://www.robot-electronics.co.uk/htm/usb_iss_tech.htm )

The ELV dongle can run up to three sensors; the IOW and ISS dongle can run only one.

The currently supported sensors and modules (for either dongle) are:
* BME280  (Temperature, Pressure, Humidity)
* LM75(B) (Temperature)
* TSL2591 (Light, visible and infrared)
* HT16K33 (LED matrix 8x8 red LEDs)

i2cusbdongles runs as data logger. It creates a log file in a CSV format. The
relative values of T, P, and H are also shown as LED columns on the LED matrix.

Included in the package is the graphing tool pytoolsPlot, which allows to
quickly plot the data during collection.

pytoolsPlot can also be used as a stand-alone plotting tool for csv data files,
with options for easy configuration and scaling.

i2cusbdongles runs in a terminal and is controlled with:
CTRL-C for stopping cleanly
CTRL-Z for showing and changing cycle time (>= 0)
CTRL-\ for plotting current logfile
       0      : no plotting; switch off if a cycle had been started
       -1     : show plot once, then off
       N (>0) : show the plot and update every N seconds

When running on Linux, i2cusbdongles also responds to single keypresses:
i   : prints info on logfile, dongles, modules, sensors
m   : take a measurement now
p   : plots the last N records, if the -l N option was given on command line
P   : plots all records
v   : prints version numbers of i2cusbdongles and Python
q   : quits i2cusbdongles

Developed on Windows, using Python 3.8
"""
#%% Imports

# NOTE: for unbuffered logging via shell use -u switch for Python:

#import serial                               # to use USB-to-Serial
import serial.tools.list_ports              # to show available serial ports
import time, sys, os, platform
import signal                               # to handle CTRL-C, etc
import getopt                               # command line options and commands
import copy
import numpy                    as np       # for array operations

cur_path = os.path.dirname(__file__)

sys.path.append(os.path.abspath(os.path.join(cur_path, "..")))
os.environ["PATH"] += os.pathsep + os.path.normpath(os.path.join(cur_path, "../../lib"))

if  sys.maxsize > 2**32:
    print('You are running a 64 bit Python interpreter')
else:
    print('You are running a 32 bit Python interpreter')

from i2cusbdongles import glob
from i2cusbdongles import  util
from i2cusbdongles.dongles.Dongle import Dongle
from i2cusbdongles.dongles import ELV
try:
    from i2cusbdongles.dongles import IOW
except ImportError:
    IOW = None
from i2cusbdongles.dongles import ISS
#import pytoolsPlot              as plot

from i2cusbdongles.sensors.SHT7x    import *
from i2cusbdongles.sensors.SCD4x     import *
from i2cusbdongles.sensors.LM75     import *
from i2cusbdongles.sensors.BME280   import *
from i2cusbdongles.sensors.TSL2591  import *
from i2cusbdongles.sensors.HT16K33     import *

# set version
glob.python_version     = sys.version.replace('\n', "")

###############################################################################

def main(datafile, configfile = glob.CONFIGFILE):
    
    # Signal handlers
    # CTRL-C : properly closes all files and devices and shuts down the program
    # CTRL-Z : shows current cycle time and allows to change it
    # CTRL-\ : plotting current logfile
    # user signals have no CTRL-? action
    signal.signal(signal.SIGTERM,  util.signal_handler)
    signal.signal(signal.SIGINT,  util.signal_handler)   # to handle CTRL-C
    if platform.system() != 'Windows':
        signal.signal(signal.SIGTSTP, util.signal_handler) # to handle CTRL-Z
        signal.signal(signal.SIGQUIT, util.signal_handler)   # to handle CTRL-\
        signal.signal(signal.SIGUSR1, util.signal_handler)   # to handle user signal1
        signal.signal(signal.SIGUSR2, util.signal_handler)   # to handle user signal2


###############################################################################
# BEGIN user activation BEGIN user activation BEGIN user activation BEGIN
###############################################################################

#%% activate any or all dongles and connected sensors
    if 0:
        glob.dongles['dummy'] = Dongle()
    
    if 0:
        print("\nactivating ELV USB-I2C dongle @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        glob.dongles['ELVdongle'] = ELV.ELVdongle()
        # glob.dongles['ELVdongle'].ELVreset()        # do a dongle software reset (takes 2 sec)
        # glob.dongles['ELVdongle'].ELVshowInfo()     # show dongle info available with '?'
        # glob.dongles['ELVdongle'].ELVshowMacro()    # show dongle content of the macro memory

        # activate the sensors connected to ELV
        if 00: glob.SHT75       ["dngl"]     = glob.dongles['ELVdongle']
        if 00: glob.SHT71       ["dngl"]     = glob.dongles['ELVdongle']
        if 00: glob.SCD40       ["dngl"]     = glob.dongles['ELVdongle']
        if 00: glob.SCD41       ["dngl"]     = glob.dongles['ELVdongle']
        if 00: glob.LM75        ["dngl"]     = glob.dongles['ELVdongle']
        if 00: glob.BME280      ["dngl"]     = glob.dongles['ELVdongle']
        if 00: glob.TSL2591     ["dngl"]     = glob.dongles['ELVdongle']
        if 00: glob.HT16K33     ["dngl"]     = glob.dongles['ELVdongle']

    if 10:
        print("\nactivating IOW-DG dongle @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")       
        
        glob.dongles['IOW-DG'] = IOW.IOWdongle(disable_pullups=glob.disable_pullups)
        
        # activate the sensors connected to IOW
        if 00: glob.SHT75        ["dngl"]     = glob.dongles['IOW-DG']
        if 00: glob.SHT71        ["dngl"]     = glob.dongles['IOW-DG']
        if 00: glob.SCD40        ["dngl"]     = glob.dongles['IOW-DG']
        if 00: glob.SCD41        ["dngl"]     = glob.dongles['IOW-DG']
        if 00: glob.LM75         ["dngl"]     = glob.dongles['IOW-DG']
        if 10: glob.BME280       ["dngl"]     = glob.dongles['IOW-DG']
        if 00: glob.TSL2591      ["dngl"]     = glob.dongles['IOW-DG']
        if 00: glob.HT16K33      ["dngl"]     = glob.dongles['IOW-DG']
        
        if glob.SHT75["dngl"] or glob.SHT71["dngl"]:
            glob.dongles['IOW-DG'] = IOW.IOWdongle(disable_pullups=glob.disable_pullups,sensibus=True)
        else:
            glob.dongles['IOW-DG'] = IOW.IOWdongle(disable_pullups=glob.disable_pullups)

        glob.dongles['IOW-DG'].IOWshowInfo() # show IDs on hard- and software, versions, etc


    if 0:
        print("\nactivating USB-ISS dongle @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        glob.dongles['ISSdongle'] = ISS.ISSdongle()
        glob.dongles['ISSdongle'].ISSshowInfo() # show IDs on hard- and software, versions, etc

        # activate the sensors connected to ISS
        if 00: glob.SHT75       ["dngl"]     = glob.dongles['ISSdongle']
        if 00: glob.SHT71       ["dngl"]     = glob.dongles['ISSdongle']
        if 00: glob.SCD40       ["dngl"]     = glob.dongles['ISSdongle']
        if 00: glob.SCD41       ["dngl"]     = glob.dongles['ISSdongle']
        if 00: glob.LM75        ["dngl"]     = glob.dongles['ISSdongle']
        if 00: glob.BME280      ["dngl"]     = glob.dongles['ISSdongle']
        if 00: glob.TSL2591     ["dngl"]     = glob.dongles['ISSdongle']
        if 00: glob.HT16K33     ["dngl"]     = glob.dongles['ISSdongle']

###############################################################################
# END user activation END user activation END user activation END
###############################################################################


#%% execute activation of the sensors on the respective dongles
    tmplt = "\nactivating {} on {} +++++++++++++++++++++++++++++++++++++++++++"

    if glob.SCD41["dngl"] != None:
        print(tmplt.format(glob.SCD41["name"], glob.SCD41["dngl"]))
        glob.SCD41['hndl'] = SensorSCD4x(glob.SCD41)
        glob.SCD41['hndl'].SCD4xInit()
        glob.SCD41['hndl'].SCD4xPerformForcedRecalibration()

    if glob.SCD40["dngl"] != None:
        print(tmplt.format(glob.SCD40["name"], glob.SCD40["dngl"]))
        glob.SCD40['hndl'] = SensorSCD4x(glob.SCD40)
        glob.SCD40['hndl'].SCD4xInit()
        glob.SCD40['hndl'].SCD4xPerformForcedRecalibration()

    if glob.SHT75["dngl"] != None:
        print(tmplt.format(glob.SHT75["name"], glob.SHT75["dngl"]))
        glob.SHT75['hndl'] = SensorSHT7x(glob.SHT75)
        glob.SHT75['hndl'].SHT7xInit()

    if glob.SHT71["dngl"] != None:
        print(tmplt.format(glob.SHT71["name"], glob.SHT71["dngl"]))
        glob.SHT71['hndl'] = SensorSHT7x(glob.SHT71)
        glob.SHT71['hndl'].SHT7xInit()

    if glob.LM75["dngl"] != None:
        print(tmplt.format(glob.LM75["name"], glob.LM75["dngl"]))
        glob.LM75['hndl'] = SensorLM75(glob.LM75)
        glob.LM75['hndl'].LM75Init()

    if glob.BME280["dngl"] != None:
        print(tmplt.format(glob.BME280["name"], glob.BME280["dngl"]))
        glob.BME280['hndl'] = SensorBME280(glob.BME280)
        glob.BME280['hndl'].BME280Init()

    if glob.TSL2591["dngl"] != None:
        print(tmplt.format(glob.TSL2591["name"], glob.TSL2591["dngl"]))
        glob.TSL2591['hndl'] = SensorTSL2591(glob.TSL2591)
        glob.TSL2591['hndl'].TSL2591Init()

    if glob.HT16K33["dngl"] != None:
        print(tmplt.format(glob.HT16K33["name"], glob.HT16K33["dngl"]))
        glob.HT16K33['hndl'] = LEDHT16K33(glob.HT16K33)
        glob.HT16K33['hndl'].HT16K33Init()
        #glob.HT16K33['hndl'].HT16K33runAllFunctions()

    print("\nactivations completed ++++++++++++++++++++++++++++++++++++++++++")


#%% prepare array for averaging
    avg_count       = 5        # average over up to avg_count cycles
    glob.sensor_vars = 0
    for sensor in glob.sensors: # automatic counting of sensor variables
        if (sensor['hndl'] is not None) and ('LED' not in sensor['feat']):
            glob.sensor_vars += len(sensor['feat'].split(","))               
        
    dummy           = np.zeros((1, glob.sensor_vars), dtype=float) # 1 row, N col
    avg_array       = copy.copy(dummy)  # begins with a single row

    # Preparing Logfiles - data will be saved with 4 decimals:
    lfnheader1      = "#Log file"
    lfnheader2      = "{:8s}, {:>19s}"
    columns         = ["#counter","DateTime"]

    #%% start data logging
    print("\nCollecting data from {:d} sensors *****************".format(glob.sensor_vars))
    counter        = 0            # cycle count
    avg_index      = 0            # will be used modulo 'avg_count' to update the data array
    timelast_cycle = time.time()  # the next cycle will be started right now
    timelast_graph = 0            # if graphcycle > 0  show 1st plot immediately
    while True:

        print("\nNew Cycle", "_"*100)
        print("DGL Sensor  XX  time      reqB   w/r_chr      info             rec")

        # BME280 data T, P, H
        try:
            t, p, h, temp_semi, press_semi, hum_semi = glob.BME280['hndl'].BME280getTPH()
            print()
            #a= 1/0
        except Exception as e:
            if glob.BME280["hndl"] is not None:
                util.exceptPrint(e, sys.exc_info(), "ERROR reading from sensor BME280")
            t, p, h, temp_semi, press_semi, hum_semi = [glob.missing_value] * 6

        # SCD41 data CO2, Temp, RH
        try:
            if glob.SCD41['hndl'].SCD4xready:
                CO2_SCD41, T_SCD41, RH_SCD41 = glob.SCD41['hndl'].SCD4xgetAll()
            else:
                CO2_SCD41, T_SCD41, RH_SCD41 = [glob.missing_value]*3
            print()
            #a = 1/0
        except Exception as e:
            if glob.SCD41["hndl"] is not None:
                util.exceptPrint(e, sys.exc_info(), "ERROR reading from sensor SCD41")
            CO2_SCD41, T_SCD41, RH_SCD41 = [glob.missing_value]*3

        # SCD40 data CO2, Temp, RH
        try:
            if glob.SCD40['hndl'].SCD4xready:
                CO2_SCD40, T_SCD40, RH_SCD40 = glob.SCD40['hndl'].SCD4xgetAll()
            else:
                CO2_SCD40, T_SCD40, RH_SCD40 = [glob.missing_value]*3
            print()
            #a = 1/0
        except Exception as e:
            if glob.SCD40["hndl"] is not None:
                util.exceptPrint(e, sys.exc_info(), "ERROR reading from sensor SCD40")
            CO2_SCD40, T_SCD40, RH_SCD40 = [glob.missing_value]*3

        # SHT75 data Temp, RH
        try:
            T_SHT75, RH_SHT75 = glob.SHT75['hndl'].SHT7xgetAll()
            print()
            #a = 1/0
        except Exception as e:
            if glob.SHT75["hndl"] is not None:
                util.exceptPrint(e, sys.exc_info(), "ERROR reading from sensor SHT75")
            T_SHT75, RH_SHT75 = [glob.missing_value]*2

        # SHT71 data Temp, RH
        try:
            T_SHT71, RH_SHT71 = glob.SHT71['hndl'].SHT7xgetAll()
            print()
            #a = 1/0
        except Exception as e:
            if glob.SHT71["hndl"] is not None:
                util.exceptPrint(e, sys.exc_info(), "ERROR reading from sensor SHT71")
            T_SHT71, RH_SHT71 = [glob.missing_value]*2

        # LM75B data Temp
        try:
            T_LM75B = glob.LM75['hndl'].LM75getTemp()
            print()
            #a = 1/0
        except Exception as e:
            if glob.LM75["hndl"] is not None:
                util.exceptPrint(e, sys.exc_info(), "ERROR reading from sensor LM75")
            T_LM75B = glob.missing_value

        # TSL2591 data Luminescence Vis, IR
        try:
            b = glob.TSL2591['hndl'].TSL2591getLumAuto()
            b1 = b[1]           # IR
            b1 = b[0] / b1      # ratio Vis / IR
            #print(b)
            #a=1/0
        except Exception as e:
            if glob.TSL2591["hndl"] is not None:
                util.exceptPrint(e, sys.exc_info(), "ERROR reading from sensor TSL2591")
            b  = [glob.missing_value] * 6
            b1 = glob.missing_value

        # store data in array for averaging
        # maximum of 13 variables; for different numbers recoding needed !
        # add one array row until total of avg_count
        if avg_array.shape[0] < avg_count and counter > 0 :
            avg_array = np.concatenate((avg_array, dummy), axis=0)


        #%% fill array at row avg_index
        i = 0
        if glob.BME280["hndl"] is not None:
            avg_array[avg_index, i] = t     # BME280 temperature
            avg_array[avg_index, i+1] = p   # BME280 humidity
            avg_array[avg_index, i+2] = h   # BME280 pressure
            if counter == 0: columns += ["T", "P", "H"]
            i+=3
        if glob.SHT75["hndl"] is not None:
            avg_array[avg_index, i] = T_SHT75       # SHT75 temperature
            avg_array[avg_index, i+1] = RH_SHT75    # SHT75 humidity
            if counter == 0: columns += ["T_SHT75", "H_SHT75"]
            i+=2
        if glob.SCD41["hndl"] is not None:
            avg_array[avg_index, i] = CO2_SCD41     # SCD41 temperature
            avg_array[avg_index, i+1] = T_SCD41     # SCD41 humidity
            avg_array[avg_index, i+2] = RH_SCD41    # SCD41 CO2
            if counter == 0: columns += ["CO2_SCD41", "T_SCD41", "H_SCD41"]
            i+=3


        if counter == 0:
            lfnheader2      += ",{:>11s}" * (len(columns) - 2)
            lfnheader2      = lfnheader2.format(*tuple(columns))           
            
            util.writeToFile(glob.logfilename, lfnheader1)
            util.writeToFile(glob.logfilename, lfnheader2)
        
            # a second logfile for experimental purposes with added extension '.avg':
            # logfile.log.avg : the data averages from the last 10 cycles
            #                   (with fewer cycles, all cycles are averaged)
            util.writeToFile(glob.logfilename + ".avg", lfnheader1)
            util.writeToFile(glob.logfilename + ".avg", lfnheader2)

        
        #mean_avg_array = np.mean(avg_array, axis=0) # average up to last mean_avg_array cycles
        mean_avg_array = np.nanmean(avg_array, axis=0) # average up to last mean_avg_array cycles

        # template for logging (4 decimals) and printing (1 decimal)
        logtmplt    = (u"{:8d}, {:19s}" + u",{: 11.4f}"   * glob.sensor_vars)
        prntmplt    = (u"{:8d}, {:19s}" + u",{: 8.1f}   " * glob.sensor_vars)

        logtext     = logtmplt.format(counter, util.strtime(), *avg_array[avg_index])
        util.writeToFile(glob.logfilename, logtext)

        logtext_avg = logtmplt.format(counter, util.strtime(), *mean_avg_array)
        util.writeToFile(glob.logfilename + ".avg", logtext_avg)

        prntext     = prntmplt.format(counter, util.strtime(), *mean_avg_array)

        print("\n        " + lfnheader2)
        util.ncprint("logtext:" + logtext,  color = glob.TCYAN)
        util.ncprint("average:" + prntext,  color = glob.TGREEN)

        # plot the data every graphcycle seconds
        if glob.graphcycle > 0:
            if time.time() - timelast_graph > glob.graphcycle:
                util.plotGraph(glob.logfilename)
                timelast_graph = time.time()

        # show relative T, P, H value on LED matrix, cols 0, 3, 6
        if glob.HT16K33['hndl'] is not None:
            try:
                #temperature
                if t is not None:
                    led_t = round((t - 20)/10 * 7)
                    glob.HT16K33['hndl'].HT16K33setCol(0, led_t )
                    glob.HT16K33['hndl'].HT16K33setCol(1, led_t )
                    print("led_t: {:2.0f}".format(led_t))

                # pressure
                if p is not None:
                    led_p = round(((p - 980) / 40 * 7))
                    glob.HT16K33['hndl'].HT16K33setCol(3, led_p )
                    glob.HT16K33['hndl'].HT16K33setCol(4, led_p )
                    print("led_p: {:2.0f}".format(led_p))

                #humidity
                if h is not None:
                    led_h = round(h/100 * 7)
                    glob.HT16K33['hndl'].HT16K33setCol(6, led_h )
                    glob.HT16K33['hndl'].HT16K33setCol(7, led_h )
                    print("led_h: {:2.0f}".format(led_h))

            except Exception as e:
                util.exceptPrint(e, sys.exc_info(), "ERROR: no led display possible")
        else:
            #print("LED Matrix not connected")
            pass

        #%% wait cycletime while checking for key presses
        while True:
            print("\rNext cycle in {:1.0f} sec". format((timelast_cycle  + glob.cycletime) - time.time() ), end="")
            #sys.stdout.flush() # not needed

            ret = util.checkForKeys()
            #print(ret)

            # don't make 2 plots if you have both p and P
            if "p" in ret:        # small cap p
                util.bell()
                util.ncprint("*** Preparing time limited plot! ***")
                util.plotGraph(glob.logfilename)

            elif "P" in ret:        # large cap p
                util.bell()
                orig = glob.plotLastValues
                glob.plotLastValues = None
                util.ncprint("*** Preparing full plot! ***")
                util.plotGraph(glob.logfilename)
                glob.plotLastValues = orig

            if "V" in ret.upper():
                util.bell()
                util.ncprint("Version status:")
                for a in util.version_status():
                    util.ncprint( "   {:15s}: {}".format(a[0], a[1]))
                print()

            if "H" in ret.upper():
                util.bell()
                util.ncprint("Help usage:")
                util.ncprint(glob.USAGE)
                print()

            if "M" in ret.upper():
                util.bell()
                util.ncprint("Take a measuremtn now")
                break

            if "Q" in ret.upper():
                util.bell()
                util.ncprint("Quit")
                util.shutdown()
                sys.exit(0)

            if "I" in ret.upper():
                util.bell()
                with open(os.path.normpath(glob.logfilename), "rt") as cfghandle:
                    llines = cfghandle.readlines()      # llines is list of lines
                util.ncprint("Info:")
                util.ncprint("   {:25s} : {}".  format("Logfile", glob.logfilename))
                util.ncprint("   {:25s} : {:,}".format("   File size (bytes)", os.path.getsize(glob.logfilename)))
                util.ncprint("   {:25s} : {:,}".format("   No of lines", len(llines)))
                util.ncprint("   {:25s} : {}".  format("Configfile", glob.configfile))
                print()
                util.ncprint("   {:25s} : {}".  format("Cycletime (sec)", glob.cycletime))
                util.ncprint("   {:25s} : {}".  format("Graphcycle (sec) (0=OFF)", glob.graphcycle))

                util.ncprint("   {:25s} : {}".  format("Last records to plot", glob.plotLastValues))
                print()
                for dongle_name, dongle in glob.dongles.items():
                    util.infoPrint(dongle, dongle_name)
                print()

            time.sleep(0.2)
            if time.time() - timelast_cycle > glob.cycletime: #Cycle time is elapsed
                timelast_cycle = time.time()
                break

        counter     += 1
        avg_index   += 1
        avg_index    = avg_index % avg_count

#%%
###############################################################################
if __name__ == "__main__":
    
    util.ncprint("#"*100) # green start line


    # parse command line options; sys.argv[0] is progname
    #print("sys.argv:", sys.argv)
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdvVPc:l:",
        ["help", "debug", "verbose", "Version", "Ports", "config", "last"])
        #print(opts, args)
    except getopt.GetoptError as e :
        # print info like "option -a not recognized", then exit
        util.ecprint("ERROR: '{}', use './pytoolsPlot -h' for help".format(e) )
        sys.exit(1)

    # processing the options
    for opt, optval in opts:

        if opt in ("-h", "--help"):
            print(glob.USAGE)
            sys.exit(0)

        elif opt in ("-d", "--debug"):
            debug = True    # not fully implemented

        elif opt in ("-v", "--verbose"):
            verbose = True    # not yet implemented

        elif opt in ("-V", "--Version"):
            print ("Version status:")
            for a in util.version_status():
                print( "   {:15s}: {}".format(a[0], a[1]))
            sys.exit(0)

        elif opt in ("-P", "--Ports"):
            print ("Available Serial Ports:")
            for a in serial.tools.list_ports.comports():
                print("  ", a)
            sys.exit(0)

        elif opt in ("-c", "--config"):
            cf = optval.strip()

            if os.path.isfile(cf):
                if os.access(cf, os.R_OK):
                    glob.configfile = cf
                else:
                    util.ecprint("ERROR config file '{}' not readable".format(cf))
                    sys.exit()
            else:
                util.ecprint("ERROR config file '{}' not found".format(cf))
                sys.exit()

        elif opt in ("-l", "--last"):
            try:
                glob.plotLastValues = int(float(optval))
            except Exception as e:
                util.ecprint("ERROR '{}' in command option: '{}' must be a number".format(e, optval))
                sys.exit()

    # processing the args for logfilename
    # With a command line argument it will be used as filename including path
    # Without a command line argument a logfilename with date&time in its
    # name in subfolder 'data' of the program folder will be created.
    #
    #print("args: len", len(args))
    if len(args) > 0:
        for arg in args:
            #print("arg:", len(arg), arg)     # so far only the Datafile is arg
            glob.logfilename = arg
    else:
        glob.logfilename = os.path.join(util.getDataPath(), "Sensor-{}.log".format(util.strtime_filename()))

    if IOW: print("{:25s}: {}".format("IOW - Using Library", IOW.iowlib))
    print("{:25s}: {}".format("Logfilename",                    glob.logfilename))
    print("{:25s}: {}".format("Plot Configuration file",        glob.configfile))

    main(glob.logfilename, configfile = glob.configfile)


