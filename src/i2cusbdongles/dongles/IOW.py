#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Code for the 'IO-Warrior Dongles' (IOW24 and IOW28)
from Code Mercenaries ( https://www.codemercs.com).
"""

import time, sys, copy
import ctypes, ctypes.util

from i2cusbdongles import glob
from i2cusbdongles import util
from i2cusbdongles.dongles.Dongle import Dongle


iowlib = ctypes.util.find_library("iowkit") # must NOT use prefix, suffix
                                            # finds: 'libiowkit.so.1'
#print("{:33s}: {}".format("IOW - Found Library", iowlib))

if not iowlib: raise ImportError("iowkit library not found in os path")

iowkit = ctypes.CDLL(iowlib)                # same result when loading:
                                            # libiowkit.so, libiowkit.so.1,
                                            # both linked to libiowkit.so.1.0.5

# iowkit definitions and declarations -----------------------------------------
# using CodeMerc doc: IO-Warrior Dynamic Library V1.5 for Windows, 22. Jul 2016
#
# IOWKIT_HANDLE IOWKIT_API IowKitOpenDevice(void);
iowkit.IowKitOpenDevice.argtypes        = None
iowkit.IowKitOpenDevice.restype         = ctypes.c_voidp

# void IOWKIT_API IowKitCloseDevice(IOWKIT_HANDLE devHandle); # devhandle ignored
# void IOWKIT_API IowKitCloseDevice(void);    # allowed also; compare with open
iowkit.IowKitCloseDevice.argtypes       = None
iowkit.IowKitCloseDevice.restype        = None

# IOWKIT_HANDLE IOWKIT_API IowKitGetDeviceHandle(ULONG numDevice);
iowkit.IowKitGetDeviceHandle.argtypes   = [ctypes.c_ulong]  # numDev = 1 ... 16
iowkit.IowKitGetDeviceHandle.restype    = ctypes.c_voidp

# ULONG IOWKIT_API IowKitGetNumDevs(void);
iowkit.IowKitGetNumDevs.argtypes        = None
iowkit.IowKitGetNumDevs.restype         = ctypes.c_ulong    # Py default

# PCHAR IOWKIT_API IowKitVersion(void);
# res like: IO-Warrior Kit V1.5
iowkit.IowKitVersion.argtypes           = None
iowkit.IowKitVersion.restype            = ctypes.c_char_p

# ULONG IOWKIT_API IowKitProductId(IOWKIT_HANDLE iowHandle);
# res like: 0x1501
iowkit.IowKitGetProductId.argtypes      = [ctypes.c_voidp]
iowkit.IowKitGetProductId.restype       = ctypes.c_ulong    # Py default

# ULONG IOWKIT_API IowKitGetRevision(IOWKIT_HANDLE iowHandle);
# res like: 0x1030
iowkit.IowKitGetRevision.argtypes       = [ctypes.c_voidp]
iowkit.IowKitGetRevision.restype        = ctypes.c_ulong    # Py default

# BOOL IOWKIT_API IowKitSetTimeout(IOWKIT_HANDLE devHandle, ULONG timeout);
iowkit.IowKitSetTimeout.argtypes        = [ctypes.c_voidp, ctypes.c_ulong]
iowkit.IowKitSetTimeout.restype         = ctypes.c_bool

# BOOL IOWKIT_API IowKitSetWriteTimeout(IOWKIT_HANDLE devHandle, ULONG timeout);
iowkit.IowKitSetWriteTimeout.argtypes   = [ctypes.c_voidp, ctypes.c_ulong]
iowkit.IowKitSetWriteTimeout.restype    = ctypes.c_bool

# ULONG IOWKIT_API IowKitWrite(IOWKIT_HANDLE devHandle, ULONG self.numPipe, PCHAR buffer, ULONG length);
iowkit.IowKitWrite.argtypes             = [ctypes.c_voidp, ctypes.c_ulong, ctypes.c_voidp, ctypes.c_ulong]
iowkit.IowKitWrite.restype              = ctypes.c_ulong    # Py default

# ULONG IOWKIT_API IowKitRead(IOWKIT_HANDLE devHandle, ULONG self.numPipe, PCHAR buffer, ULONG length);
iowkit.IowKitRead.argtypes              = [ctypes.c_voidp, ctypes.c_ulong, ctypes.c_voidp, ctypes.c_ulong]
iowkit.IowKitRead.restype               = ctypes.c_ulong    # Py default

# BOOL IOWKIT_API IowKitReadImmediate(IOWKIT_HANDLE devHandle, PDWORD value);
# Return current value directly read from the IO-Warrior I/O pins.
# not relevant for I2C
iowkit.IowKitReadImmediate.argtypes     = [ctypes.c_voidp, ctypes.POINTER(ctypes.c_ulong)]
iowkit.IowKitReadImmediate.restype      = ctypes.c_bool

# BOOL IOWKIT_API IowKitGetSerialNumber(IOWKIT_HANDLE iowHandle, PWCHAR serialNumber);
# from iowkit.h:
# typedef unsigned short *       PWCHAR;
# from library docu:
# "The serial number is represented as an Unicode string. The buffer pointed to
# by serialNumber must be big enough to hold 9 Unicode characters (18 bytes),
# because the string is terminated in the usual C way with a 0 character."
#
# Originally suggested code fails:
# iowkit.IowKitGetSerialNumber.argtypes  = [ctypes.c_voidp, ctypes.c_wchar_p]
# It results in Python crashing on conversion of c_wchar_p, probably because
# the implicit conversion of Python3 expects 4 bytes per unicode char, while
# the iowlibrary uses only 2.
# Workaround is a string buffer of length 18 and the conversion is per
# buffer.raw.decode("utf-8")
iowkit.IowKitGetSerialNumber.argtypes   = [ctypes.c_voidp, ctypes.c_voidp] # ok
iowkit.IowKitGetSerialNumber.restype    = ctypes.c_bool

# Max number of IOW devices in system = 16
IOWKIT_MAX_DEVICES                      = ctypes.c_ulong(16)

# Max number of pipes per IOW device = 2
IOWKIT_MAX_PIPES                        = ctypes.c_ulong(2)

# pipe names
IOW_PIPE_IO_PINS                        = ctypes.c_ulong(0)
IOW_PIPE_SPECIAL_MODE                   = ctypes.c_ulong(1) # use for I2C
IOW_PIPE_I2C_MODE		                = ctypes.c_ulong(2)	#only IOW28 (not IOW28L)
IOW_PIPE_ADC_MODE		                = ctypes.c_ulong(3)	#only IOW28 (not IOW28L)

# IO-Warrior vendor & product IDs
IOWKIT_VENDOR_ID                        = 0x07c0
# IO-Warrior 40
IOWKIT_PRODUCT_ID_IOW40                 = 0x1500
# IO-Warrior 24
IOWKIT_PRODUCT_ID_IOW24                 = 0x1501
IOWKIT_PRODUCT_ID_IOW24_SENSIRION       = 0x158A
# IO-Warrior 28
IOWKIT_PRODUCT_ID_IOW28                 = 0x1504
# IO-Warrior PowerVampire
IOWKIT_PRODUCT_ID_IOWPV1                = 0x1511
IOWKIT_PRODUCT_ID_IOWPV2                = 0x1512
# IO-Warrior 56
IOWKIT_PRODUCT_ID_IOW56                 = 0x1503
IOWKIT_PRODUCT_ID_IOW56_ALPHA           = 0x158B

# IOW Legacy devices open modes
IOW_OPEN_SIMPLE                         = ctypes.c_ulong(1)
IOW_OPEN_COMPLEX                        = ctypes.c_ulong(2)

IOWKIT_IO_REPORT                        = ctypes.c_ubyte * 5
IOWKIT_SPECIAL_REPORT                   = ctypes.c_ubyte * 8
IOWKIT28_IO_REPORT                      = ctypes.c_ubyte * 5
IOWKIT28_SPECIAL_REPORT                 = ctypes.c_ubyte * 64
IOWKIT56_IO_REPORT                      = ctypes.c_ubyte * 8
IOWKIT56_SPECIAL_REPORT                 = ctypes.c_ubyte * 64

#
# end iowkit definitions and declarations -------------------------------------


class IOWdongle(Dongle):
    """Code for the IO-Warrior Dongles"""

    name         = "IOW-DG"
    short        = "dongle"
    readtimeout  = 500          # ms
    writetimeout = 500          # ms  - not implemented on Linux
    
    #            IOW name    xX   time   reqB   wrt/rec   info     rec
    pTemplate = "IOW {:7s} {:2s} {:10s} [{:3d}] [{:3d}]  {:15s} == {}"


    def __init__(self, disable_pullups=False, sensibus=False):
        """opening the USB port and checking dongle"""

        # Open device and get handle
        self.iow = iowkit.IowKitOpenDevice()
        if self.iow != None:                      # must check for None, not 0 (zero)
            self.__infoprint__(str("IowKitOpenDevice"), str(self.iow), str("(iowHandle of 1st device)"))
        else:
            util.ecprint("No {} dongle detected, Exiting".format(self.name))
            sys.exit()

        # set Read Timeout
        ito = iowkit.IowKitSetTimeout(self.iow, self.readtimeout)
        self.__infoprint__("IowKitSetTimeout", ito, self.readtimeout, "ms" )

        # set Write Timeout
        iwto = iowkit.IowKitSetWriteTimeout(self.iow, self.writetimeout)
        self.__infoprint__("IowKitSetWriteTimeout", iwto, self.writetimeout, "ms - not implemented on Linux" )

        pid = iowkit.IowKitGetProductId(self.iow)
        
        if pid == IOWKIT_PRODUCT_ID_IOW28:
            self.numPipe     = IOW_PIPE_I2C_MODE
        else:
            self.numPipe     = IOW_PIPE_SPECIAL_MODE
        self.__infoprint__("Pipe Number:", "----", self.numPipe.value, "0x{:02X}".format(self.numPipe.value))

        if pid in (IOWKIT_PRODUCT_ID_IOW28, IOWKIT_PRODUCT_ID_IOW56):
            self.special_report = IOWKIT28_SPECIAL_REPORT
        else:
            self.special_report = IOWKIT_SPECIAL_REPORT

        self.reportSize  = ctypes.sizeof(self.special_report)
        self.emptyReport = self.special_report(*((0x00,)*self.reportSize))
        
        self.__infoprint__("Size of Report:", "----", self.reportSize, "0x{:02X}".format(self.reportSize))

        # Set IOWarrior to I2C mode
        self.IOWsetIOWtoI2Cmode(name=self.short, info = "setI2Cmode", disable_pullups=disable_pullups, sensibus=sensibus)

        util.fncprint("{} dongle initialized{}".format(self.name," with pull-ups disabled" if disable_pullups else ""))

        self.sensor_close_functions = []


    def IOWshowInfo(self):
        """ a run down of the IOW functions """

        print("\n---- IOWshowInfo -------------------------------------------")

        # Get individual handle
        igdh = iowkit.IowKitGetDeviceHandle(1)  # device #1
        self.__infoprint__("IowKitGetDeviceHandle(1)", igdh, "(iowHandle of 1st device)")

        # Get number of IOWs
        numdevs = iowkit.IowKitGetNumDevs()
        self.__infoprint__("IowKitGetNumDevs", numdevs)

        # Get Kit Version
        ikv = iowkit.IowKitVersion()
        self.__infoprint__("IowKitVersion", "----", "", ikv.decode("UTF-8"))

        # Get Revision
        rev = iowkit.IowKitGetRevision(self.iow)
        self.__infoprint__("IowKitGetRevision", rev, hex(rev), "Firmware Version")

        # Get ProductID and Name
        pid = iowkit.IowKitGetProductId(self.iow)
        self.__infoprint__("IowKitGetProductId", pid, hex(pid), self.__getDeviceName__(pid))

        # Get Serial number
        bsno  = ctypes.create_string_buffer(18)
        isn   = iowkit.IowKitGetSerialNumber(self.iow, ctypes.byref(bsno))
        self.__infoprint__("IowKitGetSerialNumber", isn, bsno.raw.decode("utf-8"))


    def IOWsetIOWtoI2Cmode(self, name="no name", info="no info", disable_pullups=False, sensibus=False):
        """sets IOW to I2C mode"""

        b2 = 0x80*disable_pullups + 0x40*sensibus + 0x00

        report = copy.copy(self.emptyReport)
        report[0] = 0x01 # report ID = 1
        report[1] = 0x01 # enable I2C mode
        report[2] = b2   # all flags 0 (Bit 7   - Disable Pull Ups (1 = disable) - IOW24 only (for 3.3V operation)
                         #              Bit 6   - Use Sensibus Protocol (1 = enable)
                         #              Bit 5:0 - unused, write zero
        report[3] = 0x00 # max timeout of 256x500 microsec (=0.128 sec)

        wdl = 1
        ikw = iowkit.IowKitWrite(self.iow, self.numPipe, ctypes.byref(report), self.reportSize)
        print(self.pTemplate.format(name, "TX", util.strtime()[11:], wdl, ikw, info, self.__getstrArray__(report)))



    def askDongle(self, addr, data, rbytes, wait_time=0, name="no name", info="no info", doPrint=True, end="\n"):
        """
        Send a command to the command and read data afterwards if expected
        """
        # Write & Ack command loop
        # Write to Sensor to set for reading, and read until error-free Acknowledge received,
        # but give up and break after 3 retries
        
        sensirion = (addr == 0) or (name.strip().upper().startswith("SHT7"))
        suspend_stop_flag = True if rbytes > 0 else False #True if rbytes > 0 else False
        #TODO: determine if suspend_stop_flag must be True or False if rbytes > 0              
        
        if not sensirion:

            loop = 0
            while True:
                glob.dongles[self.name].IOWwriteData(addr, data, suspend_stop_flag=suspend_stop_flag, name=name, info=info, doPrint=doPrint)
                
                ret, rep = self.IOWreadAck(name="", info="", doPrint=doPrint)
                if rep[0] == 2:             # is Acknowledge Report (ID=02)
                    if rep[1] & 0x80:       # error bit is set                        
                        print("NoACK: error bit is set")
                        if loop >= 3:
                            util.fecprint("After {} retries NoACK ignored\n".format(loop))
                            break
                        loop += 1
                    else:
                        if doPrint: print("ACK")
                        break
                else:
                    util.fecprint("wrong report ID, retrying write")
                    time.sleep(0.05) #in case acknowledgment takes some time
        
        # Write & Read loop
        sumrep = []
        if rbytes > 0:
            #For 'read' or 'send command and fetch results' sequences,
            #after writing the address and/or data to the sensor and sending the ACK bit,
            #the sensor needs the execution time to respond to the I2C read header with an ACK bit.
            #Hence, it is required to wait the command execution time before issuing the read header.            
            while True:
                if wait_time>2: time.sleep(wait_time/1000) # wait
                if sensirion:
                    glob.dongles[self.name].IOWreadCommand(addr, data[0], rbytes, name=name, info=info, doPrint=doPrint)
                else:
                    glob.dongles[self.name].IOWinitializeRead(addr, rbytes, name=name, info=info, doPrint=doPrint)
                bytes_received = 0
                while rbytes > bytes_received:
                    ret, rep = self.IOWreadData(rbytes, name="", info="", doPrint=doPrint)
                    if rep[0] == 3:
                        if rep[1] & 0x80:       # error bit is set
                            print("Error Bit set - Repeating Read")
                        else:
                            sumrep += rep[2:]
                            bytes_received += (self.reportSize-2)
                            if doPrint: print(":{:d} bytes".format(bytes_received))
                    else:
                        # sometimes repID==2 is found; loop until correct (helpful?)
                        util.ecprint("Wrong reportID - Repeating Read")
                        #time.sleep(0.5)
                break

            answ    = sumrep[:rbytes]
            stransw = ""
            for a in answ: stransw += "{:02X} ".format(a)
            if doPrint: print(" "*20, "Answer:  ==", stransw, end= end)
        else:
            if wait_time>2: time.sleep(wait_time/1000) # wait
            answ = None

        return answ


    def IOWwriteData(self, addrSensor, wdata, suspend_stop_flag=False, name= "no name", info = "no info", doPrint = True):
        """ Writing to the sensor """

        #In 7-bit addressing procedure, the slave I2C address is transferred in the 1st byte after the Start condition.
        #The first seven bits of the byte comprise the slave address.
        #The 8th bit is the read/write flag, where 0 indicates a write and 1 indicates a read.        
        addr8 = addrSensor << 1 if addrSensor else 0x00 # ex. LM75: 7bit:0x48 -> 8bit:0x90
        wdlen = len(wdata)
        stop_flag = not suspend_stop_flag
        #print("wdlen:", wdlen)

        if wdlen <= (self.reportSize-3): # all data fit into one report
            data = wdata
            if addr8: data = [addr8] + data
            ikw, report = self.IOWwriteReport(data, start=True, stop=stop_flag)
            if doPrint: print(self.pTemplate.format(name, "TX", util.strtime()[11:], wdlen + 1, ikw, info, self.__getstrArray__(report)))

        else:   # more data than fit into one report
            #print("IOWwriteData: wdata:", wdata)

            # first batch of data; with Generate Start, no Generate Stop
            pointer = (self.reportSize-3)
            data = wdata[:pointer]
            if addr8: data = [addr8] + data
            ikw, report = self.IOWwriteReport(data, start=True, stop=False)
            if doPrint: print(self.pTemplate.format(name, "TX", util.strtime()[11:], wdlen + 1, ikw, info, self.__getstrArray__(report)))

            # next batches without Start, without Stop; leave enough for one last report with Stop=True
            while pointer + (self.reportSize-2) < wdlen:
                data = wdata[pointer:pointer+(self.reportSize-2)]
                #print("pointer, data:", pointer, data)
                ikw, report = self.IOWwriteReport(data, start=False, stop=False)
                if doPrint: print(self.pTemplate.format(name, "TX", util.strtime()[11:], wdlen + 1, ikw, info, self.__getstrArray__(report)))
                pointer += (self.reportSize-2)

            # lastbatch with Stop
            data = wdata[pointer:]
            #print("pointer, last batch:", pointer, data)
            ikw, report = self.IOWwriteReport(data, start=False, stop=stop_flag)
            if doPrint: print(self.pTemplate.format(name, "TX", util.strtime()[11:], wdlen + 1, ikw, info, self.__getstrArray__(report)))


    def IOWwriteReport(self, wdata, start=True, stop=True):
        """ Write a single ID=2 report """

        #print("IOWwriteReport: wdata:", wdata)

        lenwdata = len(wdata)
        if lenwdata  > (self.reportSize-2):
            util.ecprint("Programming ERROR in IOWwriteReport: Can't write more than %d bytes in single report!" % (self.reportSize-2))
            sys.exit()

        flags = 0x00
        flags             = flags | lenwdata
        if start:   flags = flags | 0x80
        if stop:    flags = flags | 0x40
        #print("start, Stop:", start, stop, hex(flags))

        nulldata = [0x00]*(self.reportSize-2)
        data     = wdata + nulldata
        #print("IOWwriteReport: [02, " + hex(flags) + ", " + str(data[0:6]).strip("["))

        report = copy.copy(self.emptyReport)
        report[0] = 0x02    # report ID = 2
        report[1] = flags   # flags: e.g. C3:  Start, Stop and 2 bytes data + address as third byte!
                            # flags: e.g. 06:  No Start, No Stop and 6 bytes data, no address
                            # flags: e.g. 84:  Start, No Stop and 4 bytes data, including address
                            # flags: e.g. 46:  No Start, Stop and 6 bytes data, no address
                            # flags contains the following bits:
                            # 7 - Generate Start
                            # 6 - Generate Stop
                            # 5 - unused, write zero
                            # 4 - unused, write zero
                            # 3 - unused, write zero
                            # 2 - data count MSB
                            # 1 - data count
                            # 0 - data count LSB 
        
        for i in range(0,self.reportSize-2): report[i+2] = data[i]
        
        ikw = iowkit.IowKitWrite(self.iow, self.numPipe, ctypes.byref(report), self.reportSize)

        return ikw, report

    def IOWreadAck(self, name="", info="", doPrint=True):
        """ Receives acknowledgement ID=2 report via endpoint 2 """

        return self.IOWreadData(rbytes=2, name=name, info=info, doPrint=doPrint)
    

    def IOWreadData(self, rbytes, name="", info="", doPrint=True):
        """ Read max of (self.reportSize-2) bytes from sensor """

        report = copy.copy(self.emptyReport)
        ikr = iowkit.IowKitRead(self.iow, self.numPipe, ctypes.byref(report), self.reportSize)
        if doPrint: print(self.pTemplate.format(name, "RX", util.strtime()[11:], rbytes, ikr, info, self.__getstrArray__(report)), end="")

        return ikr, report


    def IOWinitializeRead(self, addrSensor, count, name="no name", info="no info", doPrint=True):
        """ Setup Sensor with 7bit address addrSensor for Read of count bytes"""
        
        #Call to general function with command = 0, so that only the sensor address is written
        return self.IOWreadCommand(addrSensor, 0x00, count, name=name, info=info, doPrint=doPrint)


    def IOWreadCommand(self, addrSensor, command, count, name="no name", info="no info", doPrint=True):
        """
        Write a ID=3 report at sensor address with read command, to receive count bytes
        This function is documented in the IOWarrior datasheet, and essential for the SHT7x sensor
        """

        #In 7-bit addressing procedure, the slave address is transferred in the 1st byte after the Start condition.
        #The 1st seven bits of the byte comprise the slave address.
        #The 8th bit is the read/write flag, where 0 indicates a write and 1 indicates a read.
        addr8  = ((addrSensor << 1) + 1) if addrSensor else 0x00  # ex. LM75: 7bit:0x49 -> 8bit:0x91
        
        report = copy.copy(self.emptyReport)
        report[0] = 0x03  # report ID = 3
        report[1] = count # count: (=number of bytes to be read from the sensor)
        report[2] = addr8|command # sensor read address + command
        
        ikw = iowkit.IowKitWrite(self.iow, self.numPipe, ctypes.byref(report), self.reportSize)
        if doPrint: print(self.pTemplate.format("", "cR" if command else "iR", util.strtime()[11:], count, ikw, info, self.__getstrArray__(report)))


    def close(self):
        """ a dummy just for symmetry """
        pass
        print("IOW is closed")


    def __getstrArray__(self, report):
        """ return report array as string of hexadecimal, excepted the last zeros"""
    
        i = len(report)-1
        sr = ["{:02X} ".format(report[i])]
        while report[i] == 0x00 and i > 0: i = i - 1
        if i < len(report)-2:
            sr += ["..."]
        else:    
            i = len(report)-2
            
        sr += ["{:02X} ".format(report[j]) for j in range(i, -1, -1)]
    
        return "".join(reversed(sr))


    def __getDeviceName__(self, pid):
        """ returns name of Device """

        if   pid == IOWKIT_PRODUCT_ID_IOW24:
            itype = "24"
        elif pid == IOWKIT_PRODUCT_ID_IOW24_SENSIRION :
            itype = "24-Sensirion"
        elif pid == IOWKIT_PRODUCT_ID_IOW28:
            itype = "28"
        elif pid == IOWKIT_PRODUCT_ID_IOW40:
            itype = "40"
        elif pid == IOWKIT_PRODUCT_ID_IOW56:
            itype = "56"
        else:
            itype = " (unknown)"

        return "IO-Warrior{}".format(itype)


    def __infoprint__(self, text, ret, *args):
        """ print results """

        sarg = ""
        for arg in args: sarg += "{:16s} ".format(str(arg))
        print("{:30s}: {:5s} {:15s}".format(text, str(ret), sarg))

