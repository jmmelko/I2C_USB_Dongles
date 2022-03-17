#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Code for the Devantech USB-ISS Dongle (https://devantech.co.uk/)
"""

import sys, serial, time

#from I2Cpytools import glob
from i2cusbdongles import util
from i2cusbdongles.dongles.Dongle import Dongle

class ISSdongle(Dongle):
    """Code for the ISS USB-I2C Dongle"""

    name        = "ISSdongle"
    short       = "dongle"

    # Serial port
    ser         = None                  # serial port pointer
    baudrates   = [1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200]
    baudrate    = baudrates[9]          # 115200
    usbport     = "/dev/ttyACM0"        #
    timeout     = 0.2                   # what is needed?

    #              ISS name    xX   time   reqB   wrt/rec   info     rec
    pTemplate   = "ISS {:7s} {:2s} {:10s} [{:3d}] [{:3d}]  {:20s} == {}"

    def __init__(self):
        """opening the serial port and testing for correct dongle"""

        # open serial port
        try:
            self.ser = serial.Serial(self.usbport, self.baudrate, timeout=self.timeout)
            print("ISS dongle  ", end="")
            util.ncprint("opened at serial port: {} (baudrate:{}, timeout: {} sec)".format(self.usbport, self.baudrate, self.timeout))
        except Exception as e:
            util.exceptPrint(e, sys.exc_info(), "ERROR Serial port for ISS dongle could not be opened")
            util.ecprint("Is ISS dongle connected? - Exiting")
            sys.exit(1)

        # Test on correct module ID
        self.ISSwriteAdmin(b'\x5A\x01', name=self.short, info="Get ISS Version")
        rec = self.ISSreadAdmin(length=3)
        if rec[0] == 0x07:
            util.fncprint("ISS Dongle initialized")
        else:
            util.fecprint("ISS Dongle did not respond - is it connected?")
            sys.exit(1)

        # default is software I2C mode
        if 10:  # Set I2C Mode for hardware I2C at 100kHz
            self.ISSwriteAdmin(b'\x5A\x02\x60\x04', name=self.short, info="Set I2C mode")
            rec = self.ISSreadAdmin(length=2)
            if rec == b'\xff\x00':
                util.fncprint("ISS Dongle set to hardware mode, 100kHz")
            else:
                util.fecprint("ISS Dongle setting to hardware I2C mode, 100kHz - FAILED")
                sys.exit(1)

        else: # Set I2C Mode for software I2C at 100kHz (default mode)
            self.ISSwriteAdmin(b'\x5A\x02\x40\x04', name=self.short, info="Set I2C mode")
            rec = self.ISSreadAdmin(length=2)
            if rec == b'\xff\x00':
                util.fncprint("ISS Dongle set to hardware mode, 100kHz")
            else:
                util.fecprint("ISS Dongle setting to hardware I2C mode, 100kHz - FAILED")
                sys.exit(1)


    def ISSshowInfo(self):
        """Show the startup info"""

        print("\n---- Show Info")

        # Module ID, Firmware Version, Operating Mode
        self.ISSwriteAdmin(b'\x5A\x01', name=self.short, info="Get ISS Version")
        rec = self.ISSreadAdmin()
        util.fncprint("ISS Version: Module ID:       0x{:02X}".format(rec[0] ))
        util.fncprint("ISS Version: Firmware :       0x{:02X}".format(rec[1] ))
        util.fncprint("ISS Version: Operating Mode:  0x{:02X}".format(rec[2] ))
        util.fncprint("Note: Operating Mode 0x40 is: I2C_S_100kHz (Software Mode)")
        util.fncprint("Note: Operating Mode 0x60 is: I2C_H_100kHz (Hardware Mode)")

        # Serial Number
        self.ISSwriteAdmin(b'\x5A\x03', name=self.short, info="Get Serial Number")
        rec = self.ISSreadAdmin()
        util.fncprint("Serial Number:", rec.decode("utf-8") )


    def ISSwriteAdmin(self, command, name= "-", info = "no info"):
        """ write to the USB-ISS - only for its interal admin functions"""

        wrt     = self.ser.write(command)  # wrt = no of bytes written
        print( self.pTemplate.format(name, "TA", util.strtime()[11:], len(command), wrt, info, self.__strCommand(command)))


    def ISSreadAdmin(self, length = 100, name = "", info = "", doPrint=True):
        """ read from the USB-ISS"""

        rec = self.ser.read(length )
        cnt = self.ser.in_waiting
        if cnt > 0:
            print("7Bytes waiting:", cnt)
            while True:                # read single byte until nothing is returned
                x = self.ser.read(1)
                if len(x) == 0: break
                rec += x

        if doPrint: print( self.pTemplate.format(name, "RA", util.strtime()[11:], length, len(rec), info, self.__strCommand(rec)))

        return rec


    def askDongle(self, addr, data, rbytes, wait_time=0, name= "no name", info = "no info", doPrint= True, end="\n"):
        """takes care of the communication needs of the dongle"""

        self.ISSwriteData(addr, data, name=name, info=info, doPrint=doPrint)
        if rbytes > 0:
            if wait_time>2: time.sleep(wait_time/1000) 
            self.ISSinitializeRead(addr, data, rbytes, name=name, info=info, doPrint=doPrint)
            answ = self.ISSreadData (length=rbytes, name=name, doPrint=doPrint)
            if doPrint: print(end=end)
        else:
            answ = None

        return answ


    def ISSwriteData (self, addr, data, name= "--", info = "---", doPrint=True):
        """write commands for the sensors via the ISS USB-I2C"""

        waddr8  = (addr << 1) + 0
        wdata   = b""
        for a in data: wdata += bytes([a])
        command = b'\x55' + bytes([waddr8]) + wdata
        wrt     = self.ser.write(command)  # wrt = no of bytes written

        if doPrint: print(self.pTemplate.format(name, "TX", util.strtime()[11:], len(command), wrt, info, self.__strCommand(command)))


    def ISSinitializeRead(self, addr, register, count, name= "no name", info = "no info", doPrint = True):
        """ Setup Sensor with address addrSensor for reading count bytes;
        attempts workaround for ISS problem"""

        raddr8  = (addr << 1) + 1

        # is this a fix for the faulty ISS needs?
        # different command 0x56 (vs 0x55) for 2 vs 1 byte sequence
        # What if 3 bytes are needed?
        if len(register) <= 1 :
            # 1 byte
            command = b'\x55' + bytes([raddr8]) + bytes(register) + bytes([count])
            ii = "i1"
        else:
            # 2 bytes (and more -> problem?)
            command = b'\x56' + bytes([raddr8]) + bytes(register) + bytes([count])
            ii = "i2"

        wrt     = self.ser.write(command)  # wrt = no of bytes written
        if doPrint: print(self.pTemplate.format(name, ii, util.strtime()[11:], count, wrt, info, self.__strCommand(command) ))


    def ISSreadData (self, length = 100, name = "", info = "", doPrint=True):
        """ read from the USB-ISS"""

        rec = self.ser.read(length)
        cnt = self.ser.in_waiting
        if cnt > 0:
            print("\7Bytes waiting:", cnt)
            while True:            # read single byte until nothing is returned
                x = self.ser.read(1)
                if len(x) == 0: break
                rec += x

        if doPrint: print(self.pTemplate.format("", "RX", util.strtime()[11:], length, len(rec), info, self.__strCommand(rec)), end="")

        reclist = []
        for a in rec: reclist.append(a)

        return reclist


    def ISSreset(self):
        """ Reset the ISS dongle """

        print("\n---- Reset")
        print("not implemented in module")


    def close(self):
        """ Close the serial port """

        self.ser.close()
        print("ISS is closed")


    def __strCommand(self, command):
        """Convert Bytes sequence to Hex string"""

        scmd = ""
        for a in command: scmd += "{:02X} ".format(a)

        return str(command) + " == " + scmd
