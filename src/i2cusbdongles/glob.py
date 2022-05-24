#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Global variables for i2cusbdongles
"""

import sys, os
PLATFORM = sys.platform
os.system('color') # to enable ansi escape characters for color codes

# Versions and infos
__author__          = "jmmelkon"
__copyright__       = "Copyright 2022"
__credits__         = [""]
__license__         = "GPL"
__version__         = "i2cusbdongles-1.1"   # forking from I2CpyTools by ullix

python_version      = ""                    # eg 3.7

# flags
debug               = True                 # helpful for debugging, use via command line, partially implemented
verbose             = True                 # more detailed printing, use via command line, not implemented yet

# dir & file
dataDirectory       = "data"                # the data subdirectory to the program directory

CONFIGFILE          = "cfg/pytoolsPlot.cfg" # default config file
configfile          = CONFIGFILE

#%% Dongles

#Beware that None is not a pointer, so updating this dict will not update objects referring directly to its values
dongles = {'ELVdongle': None, 'IOW-DG': None, 'ISSdongle': None, 'dummy': None}

disable_pullups = True                      # To disable pull-ups transistors of the dongle, if alreayd present on the sensor PCB
# ELV USB-I2C Dongle
# IO-Warrior24 Dongle (IOW-DG)
# USB-ISS Dongle Devantech

# Sensors and Modules

LM75                = {
                       "name": "LM75",
                       "feat": "Temperature",
                       "addr": 0x48,        # (d72) addr:0x48 ... 0x4F
                       "type": "LM75B",     # options: "LM75", "LM75B"
                       "hndl": None,        # handle
                       "dngl": None,        # connected with dongle
                      }

BME280              = {
                       "name": "BME280",
                       "feat": "Temperature, Pressure, Humidity",
                       "addr": 0x77,        # (d119)  addr: 0x76, 0x77
                       "type": 0x60,        # (d96)   BME280 has chip_ID 0x60
                       "hndl": None,        # handle
                       "dngl": None,        # connected with dongle
                      }

TSL2591             = {
                       "name": "TSL2591",
                       "feat": "Vis, IR",
                       "addr": 0x29,        # (d41)  addr: 0x29
                       "type": 0x50,        # Device ID 0x50
                       "hndl": None,        # handle
                       "dngl": None,        # connected with dongle
                      }

HT16K33             = {
                       "name": "HT16K33",
                       "feat": "LED Matrix 8x8",
                       "addr": 0x70,        # (d112) addr: 0x70 ... 0x77
                       "type": "LED8x8",    # no ID found in docs
                       "hndl": None,        # handle
                       "dngl": None,        # connected with dongle
                      }

SHT75             = {
                       "name": "SHT7x",
                       "feat": "Temperature, Humidity",
                       "addr": 0x00,        # 0, because device is not I²C compliant
                       "type": "SHT75",     # more precise
                       "hndl": None,        # handle
                       "dngl": None,        # connected with dongle
                      }

SHT71             = {
                       "name": "SHT7x",
                       "feat": "Temperature, Humidity",
                       "addr": 0x00,        # 0, because device is not I²C compliant
                       "type": "SHT71",     # less precise
                       "hndl": None,        # handle
                       "dngl": None,        # connected with dongle
                      }

SCD40             = {
                       "name": "SCD40",
                       "feat": "CO2, Temperature, Humidity",
                       "addr": 0x62,        # found in the docs
                       "type": "SCD40",     # less precise, no single shot
                       "hndl": None,        # handle
                       "dngl": None,        # connected with dongle
                      }

SCD41             = {
                       "name": "SCD41",
                       "feat": "CO2, Temperature, Humidity",
                       "addr": 0x62,        # found in the docs
                       "type": "SCD41",     # More precise, single-shot possible
                       "hndl": None,        # handle
                       "dngl": None,        # connected with dongle
                      }

#%% Sensors
sensors = [LM75, BME280, TSL2591, HT16K33, SHT75, SHT71, SCD40, SCD41] # All sensor objects


sensor_vars         = None                    # number of variables measured from
                                            # the sensors and logged to file
                                            # needs code changes in i2cusbdongles
                                            # if number changes (see array)
missing_value       = None                  # value to use if it can't be measured
                                            # will be in the log file as 'nan'
#%%
# Logging
cycletime           = 5.0                  # time to sleep in measurement loop;
                                            # show and change with 'CTRL-Z'
logfilename         = ""                    # name of the log file
logfile             = None                  # file handler of logfilename

# Graphic
graphcycle          = 0                     # cycletime for the graph updates
                                            # 0 (zero) switches updates off
                                            # show and change with 'CTRL-\'
subx                = None                  # subprocess pytoolsPlot.py object
subxpid             = None                  # PID of subprocess pytoolsPlot.py
plotLastValues      = None                  # if != None the only the last
                                            # plotlastvalues will be plotted




#colors for the terminal
# https://gist.github.com/vratiu/9780109
TCYAN               = '\033[96m'            # cyan
tPURPLE             = '\033[95m'            # purple (dark)
tBLUE               = '\033[94m'            # blue (dark)
TGREEN              = '\033[92m'            # light green
TYELLOW             = '\033[93m'            # yellow
TRED                = '\033[91m'            # red
TDEFAULT            = '\033[0m'             # default, i.e greyish
BOLD                = '\033[1m'             # white (bright default)
UNDERLINE           = '\033[4m'             # underline
BOLDREDUL           = '\033[31;1;4m'        # bold, red, underline
BOLDRED             = '\033[31;1m'          # bold, red - but is same as TRED

NORMALCOLOR         = TDEFAULT              # normal printout
HILITECOLOR         = TGREEN                # hilite message
ERRORCOLOR          = TYELLOW               # error message

# help info
USAGE = """
Usage:  I2Cpytools [Options] Datafile

Options:
    -h, --help          Show this help and exit
    -d, --debug         Run with printing debug info
                        Default is debug = False
    -v, --verbose       Be more verbose
                        Default is verbose = False
    -V, --Version       Show version status and exit
    -P, --Ports         Show available serial ports and exit
    -c, --config name   Set the plotting config file to name;
                        name is the config file incl. path
                        Default is 'cfg/pytoolsPlot.cfg'
    -l, --last N        Plot only the last N records

Datafile                File must be of type CSV
                        (Comma Separated Values)
                        If data file is not in same
                        directory as program, a relatve
                        or absolute path must be given:
                        e.g.: path/to/csvfile4plotting
"""
