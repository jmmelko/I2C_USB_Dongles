#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Code for the ELV USB-I2C Dongle
"""

import sys, serial, time

#from I2Cpytools import glob
from i2cusbdongles import util
from i2cusbdongles.dongles.Dongle import Dongle

class ELVdongle(Dongle):
    """Code for the ELV USB-I2C Dongle"""

    name        = "ELVdongle"
    short       = "dongle"

    # Serial port
    ser         = None                  # serial port handle
    baudrates   = [1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200]
    baudrate    = baudrates[9]          # 115200
    usbport     = '/dev/ttyUSB0'        #
    timeout     = 0.2                   # what is needed?

    #              ELV name    xX   time   reqB   wrt/rec   info     rec
    pTemplate   = "ELV {:7s} {:2s} {:10s} [{:3d}] [{:3d}]  {:20s} == {}"

    def __init__(self):
        """opening the serial port and testing for correct dongle"""

        # open serial port
        try:
            self.ser = serial.Serial(self.usbport, self.baudrate, timeout=self.timeout)
            print("ELV dongle  ", end="")
            util.ncprint("opened at serial port: {} (baudrate:{}, timeout: {} sec)".format(self.usbport, self.baudrate, self.timeout))
        except Exception as e:
            util.exceptPrint(e, sys.exc_info(), "ERROR Serial port for ELV dongle could not be opened")
            util.ecprint("Is ELV dongle connected? - Exiting")
            sys.exit(1)

        # stop macro '<') and set 'y30' (in order to NOT get ACK and NACK)
        # and get info by '?'
        self.ELVwriteAdmin(b'<y30?', name=self.short, info="Init Dongle")
        rec = self.ELVreadAdmin(140, name=self.short, info="").strip()
        if rec.startswith(b"ELV"):
            util.fncprint("ELV Dongle initialized")
        else:
            util.fecprint("ELV Dongle did not respond - is it connected?")
            sys.exit(1)


    def ELVreset(self):
        """Reset the ELV dongle (takes 2 sec!)"""

        print("\n---- Reset")
        self.ELVwriteAdmin(b'z4b', name=self.short, info="Reset Dongle")
        time.sleep(2) # 1 sec is NOT enough
        rec = self.ELVreadAdmin(name=self.short, info="")
        print(rec.decode("utf-8") )


    def ELVshowInfo(self):
        """Show the startup info"""

        print("\n---- Show Info")
        self.ELVwriteAdmin(b'?', name=self.short, info="Show Info")
        rec = self.ELVreadAdmin(140, name=self.short, info="").strip()
        print(rec.decode("utf-8") )


    def ELVshowMacro(self):
        """ Print the Macro in Memory """

        print("\n---- Show Macrocode")
        self.ELVwriteAdmin(b'U', name=self.short, info="Show Macrocode" )
        rec = self.ELVreadAdmin(255+26, name=self.short, info="")
        rd = (rec.decode("utf-8")).split("\r\n")
        print(rd[0])
        for i in range(0, len(rd[1]),64):
            print(rd[1][i:i+64], "|")
        print(rd[2])


    def ELVwriteAdmin (self, command, name= "-", info = "no info"):
        """write to the ELV USB-I2C - only for its interal admin functions"""

        command = command.upper()
        wrt     = self.ser.write(command)  # wrt = no of bytes written
        print( self.pTemplate.format(name, "TA", util.strtime()[11:], len(command), wrt, info, command))


    def ELVreadAdmin (self, length = 100, name = "-", info = "no info"):
        """read from the ELV USB-I2C - only for its internal admin functions"""

        rec = self.ser.read(length)
        cnt = self.ser.in_waiting
        if cnt > 0:
            util.bell()
            print("Bytes waiting:", cnt)
            while True:            # read single byte until nothing is returned
                x = self.ser.read(1)
                if len(x) == 0: break
                rec += x
        print("ELVreadAdmin: len(rec), rec:", len(rec), rec)
        rec = rec.strip()
        print( self.pTemplate.format(name, "RA", util.strtime()[11:], length, len(rec), info, rec))

        return rec


    def askDongle(self, addr, data, rbytes, wait_time=0, name="no name", info="no info", doPrint=True, end="\n"):
        """ Function doc """

        self.ELVwriteData(addr, data, name=name, info=info, doPrint=doPrint)
        if rbytes > 0:
            if wait_time>2: time.sleep(wait_time/1000)
            self.ELVinitializeRead(addr, rbytes, name=name, doPrint=doPrint)
            answ = self.ELVreadData(length=rbytes, name=name, doPrint=doPrint)
            if doPrint: print(end=end)
        else:
            answ = None

        return answ


    def ELVwriteData (self, addr, data, name="", info ="", doPrint=True):
        """write commands for the sensors via the ELV USB-I2C"""

        wA      = "{:02X}".format((addr << 1) + 0)
        wdata   = ""
        for a in data: wdata += " {:02X}".format(a) # puts a space at the beginning

        command = bytes('S {}{} P'.format(wA, wdata), 'ASCII').upper()
        wrt     = self.ser.write(command)  # wrt = no of bytes written
        if doPrint: print(self.pTemplate.format(name, "TX", util.strtime()[11:], len(command), wrt, info, command))


    def ELVinitializeRead(self, addr, rbytes, name="", info="", doPrint=True):
        """initialize reading from the sensor via the ELV USB-I2C"""

        rA      = "{:02X}".format((addr << 1) + 1)  # read address
        rb      = "{:02X}".format(rbytes)           # no of bytes
        command = bytes('S {} {} P'.format(rA, rb), 'ASCII').upper()
        wrt     = self.ser.write(command)  # wrt = no of bytes written
        if doPrint: print(self.pTemplate.format("", "iR", util.strtime()[11:], len(command), wrt, info, command))


    def ELVreadData (self, length=1, name="", info="", doPrint=True):
        """ read data from the ELV USB-I2C """

        rec = self.ser.read(length * 3 + 2) # 3 chars per byte('FF ') + CR, LF
        cnt = self.ser.in_waiting
        if cnt > 0:
            util.bell()
            print("Bytes waiting:", cnt)
            while True:                # read single byte until nothing is returned
                x = self.ser.read(1)
                if len(x) == 0: break
                rec += x

        rec = rec.rstrip(b"\r\n")       # remove carridge return, linefeed, keep last space

        if doPrint: print( self.pTemplate.format("", "RX", util.strtime()[11:], length, len(rec), info, rec), end="")

        if not rec.strip().startswith(b"Solve ") or \
           not rec.strip().startswith(b"Err: "):        # conversion unless an error msg from dongle
            rlist = self.__getListfromRec(rec)
            return rlist
        else:
            return rec


    def close(self):
        """ Close the serial port """

        self.ser.close()
        print("ELV is closed")


    def __getListfromRec(self, rec):
        """ convert ASCII string from terminal to list of integer """
        # rec    : b'BE 6E 9A 69 32 00 ...'
        # returns: [190, 110, 154, 105, 50, 0, ...]

        rlist = []
        if len(rec) >= 3:
            for i in range(0, len(rec), 3):
                rlist.append(int(rec[i:i+3], 16))
        else: # empty record
            pass

        return rlist
