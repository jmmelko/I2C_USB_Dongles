#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
I2C sensor module LM75(B)
"""

import sys

from i2cusbdongles import glob
from i2cusbdongles import util
"""
LM75B Digital temperature sensor and thermal watchdog
LM75:   9 bit resolution
LM75B: 11 bit resolution
https://www.nxp.com/docs/en/data-sheet/LM75B.pdf
"""

#activating LM75 on ELVdongle +++++++++++++++++++++++++++++++++++++++++++
#ELV LM75    TX 12:47:18   [  9] [  9]  Init Sensor Reg      == b'S 90 00 P'                # send 2 bytes, addr90+00
#ELV LM75    iR 12:47:18   [  9] [  9]                       == b'S 91 02 P'                # prep for reading 2 bytes from addr 91
#ELV LM75    RX 12:47:18   [  2] [  6]                       == b'1A A0 '                   # get 2 bytes 1A 80 = 26.5°C

#activating LM75 on IOW-DG +++++++++++++++++++++++++++++++++++++++++++
#IOW LM75    TX 13:11:35   [  2] [  8]  Init Sensor Reg      == 02 C2 90 00 00 00 00 00     # send 2 bytes, addr90+00
#IOW         RX 13:11:35   [  2] [  8]                       == 02 02 00 00 00 00 00 00 ACK # ack
#IOW LM75    iR 13:11:35   [  2] [  8]                       == 03 02 91 00 00 00 00 00     # prep for reading 2 bytes from addr 91
#IOW         RX 13:11:35   [  2] [  8]                       == 03 02 1A 80 00 00 00 00     # get 2 bytes 1A 80 = 26.5°C

#activating LM75 on ISSdongle +++++++++++++++++++++++++++++++++++++++++++
# the I2C official way, NOT working !!!
#ISS LM75    TX 12:59:50   [  3] [  3]  Init Sensor Reg      == b'U\x90\x00' == 55 90 00    # send 2 bytes, addr90+00
#ISS LM75    iR 12:59:50   [  2] [  3]                       == b'U\x91\x02' == 55 91 02    # prep for reading 2 bytes from addr 91
#ISS LM75    RX 12:59:50   [  2] [  0]                       == b'' ==                      # get nothing

#activating LM75 on ISSdongle +++++++++++++++++++++++++++++++++++++++++++
# with ISS specific workaraound
#ISS LM75    TX 12:57:44   [  3] [  3]  Init Sensor Reg      == b'U\x90\x00' == 55 90 00    # send 2 bytes, addr90+00
#ISS LM75    iR 12:57:44   [  2] [  4]                       == b'U\x91\x00\x02' == 55 91 00 02 # prep for reading 2 bytes from addr 91 AND set reg 00!
#ISS LM75    RX 12:57:44   [  2] [  2]                       == b'\x1a\x80' == 1A 80        # get 2 bytes 1A 80 = 26.5°C




class SensorLM75:
    """Code for the LM75(B) sensors"""

    def __init__(self, LM75):
        self.dongle  = LM75["dngl"]    # "ELVdongle", "IOW-DG", "ISSdongle"
        self.addr    = LM75["addr"]    # addr:0x48 ... 0x4F
        self.subtype = LM75["type"]    # "LM75" or "LM75B"
        self.name    = LM75["name"]    # "LM75"


    def LM75Init(self):
        """Send address and write to register 00.
        Reading gives 1st temp value of 2 bytes"""

        data    = [0x00]
        rbytes  = 2
        try:
            answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Init Sensor Reg")
        except Exception as e:
            util.exceptPrint(e, sys.exc_info(), "ERROR initialzing sensor {} at dongle {}".format(self.name, self.dongle))
            util.ecprint("Is sensor connected? - Exiting")
            sys.exit()


    def LM75getTemp(self):
        """ Write to reg 00 and read the temp """

        data     = [0x00]
        rbytes   = 2
        answ     = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="get Temp", end="")
        msb, lsb = answ[0], answ[1]
        temp     = self.__calcTemperature(msb, lsb)
        util.ncprint("                       Result: T: {:6.3f}".format(temp), color=glob.TDEFAULT)

        return temp


    def __calcTemperature (self, msb, lsb):
        """
        returns Temp in deg Celsius calculated from msb, lsb
        - use 11 bit conversion for LM75B,
        -      9 bit conversion for LM75
        temp is in 2 bytes in Two's complement
        """
        #11-bit binary
        #(two’s complement) Hexadecimal Value
        #011 1111 1000      3F8         +127.000 °C
        #011 1111 0111      3F7         +126.875 °C
        #011 1111 0001      3F1         +126.125 °C
        #011 1110 1000      3E8         +125.000 °C
        #000 1100 1000      0C8         + 25.000 °C
        #000 0000 0001      001         +  0.125 °C
        #000 0000 0000      000            0.000 °C
        #111 1111 1111      7FF         -  0.125 °C
        #111 0011 1000      738         - 25.000 °C
        #110 0100 1001      649         - 54.875 °C
        #110 0100 1000      648         - 55.000 °C

        if self.subtype == "LM75B": # 11bit
            temp1 = ((msb << 8 | lsb ) >> 5)
            if temp1 & 0x400:               # 0b100 0000 0000
                temp1 = temp1 - 0x800       # 0b1000 0000 0000
            temp  = temp1 * 0.125           # deg Celsius  for LM75B (11bit)

        else:                       # 9 bit
            temp1 = ((msb << 8 | lsb ) >> 7)
            if temp1 & 0x100:               # 0b1 0000 0000
                temp1 = temp1 - 0x200       # 0b10 0000 0000
            temp  = temp1 * 0.5             # deg Celsius  for LM75 ( 9bit)

        return temp

    def close(self):
        
        pass