#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
I2C sensor module SHT7x
"""

import sys

from i2cusbdongles import glob
from i2cusbdongles import util

"""
SHT71
SHT75: more precise
https://www.sensirion.com/en/environmental-sensors/humidity-sensors/pintype-digital-humidity-sensors/

"""


class SensorSHT7x:
    """Code for the SHT71/SHT75 sensors"""

    def __init__(self, SHT7x):
        self.dongle  = SHT7x["dngl"]    # "ELVdongle", "IOW-DG", "ISSdongle"
        self.addr    = SHT7x["addr"]    # addr:0x48 ... 0x4F
        self.subtype = SHT7x["type"]    # "SHT71" or "SHT75"
        self.name    = SHT7x["name"]    # "SHT7x"


    def SHT7xInit(self):
        """Send address and write to register 00."""

        data    = [0x03]
        rbytes  = 0 # no data is expected, just an acknowledgement
        try:
            answ = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Init Sensor Reg")
        except Exception as e:
            if glob.debug:
                raise e                
            else:
                util.exceptPrint(e, sys.exc_info(), "ERROR initializing sensor {} at dongle {}".format(self.name, self.dongle))
                util.ecprint("Is sensor connected? - Exiting")
                
            sys.exit()

    def SHT7xSoftReset(self):
        """Send address and write to register 00."""

        data    = [0x1E]
        rbytes  = 3
        try:
            answ = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Sensor Soft reset")
        except Exception as e:
            util.exceptPrint(e, sys.exc_info(), "ERROR resetting sensor {} at dongle {}".format(self.name, self.dongle))
            util.ecprint("Is sensor connected? - Exiting")
            sys.exit()
            
        return answ

    def SHT7xgetTemp(self):
        """ Write to reg 00 and read the temp """

        data     = [0x03]
        rbytes   = 3
        answ     = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="get Temp", end="")
        soT, CRC = self.__parse_BigEndianData__(answ)
        temp     = self.__calcTemperature__(soT)
        util.ncprint(" "*10 + "Result: T = {:6.3f}".format(temp), color=glob.TDEFAULT)

        return temp

    def SHT7xgetRH(self, temp=None):     
        """ Write to reg 00 and read the humidity """

        if not temp: temp = self.SHT7xgetTemp()
        
        data     = [0x05]
        rbytes   = 3
        answ     = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="get RH", end="")
        soRH, CRC = self.__parse_BigEndianData__(answ)
        RH     = self.__calcHumidity__(soRH, temp)
        util.ncprint(" "*10 + "Result: RH = {:6.3f}".format(RH), color=glob.TDEFAULT)

        return RH
    
    def SHT7xgetAll(self):
        
        temp = self.SHT7xgetTemp()
        RH = self.SHT7xgetRH(temp)
        return temp, RH
    
    def close(self):
        
        pass
    
    def __parse_BigEndianData__(self, BigEndianArray):
        """
        Converts BigEndian byte array [LSB, MSB, CRC] to decimal values
        """       
        meas = BigEndianArray[0]<<8 | BigEndianArray[1]
        if len(BigEndianArray) > 2:
            CRC = BigEndianArray[2]
        else:
            CRC = 0
        
        return meas, CRC

    def __calcTemperature__(self, soT):
        """
        returns Temp in deg Celsius calculated from rawTemp in Little Endian
        """
        return -39.66 + (0.01*soT)  #For 3.3V VDD

    def __calcHumidity__(self, soRH, temp):
        """
        returns humidity in % calculated from sensor humidity value in Little Endian
        and from previously-measured temperature in °C
        """        
        RHlin = -2.0468 + 0.0367*soRH + (-1.5955e-6)*(soRH**2) # linearisation
        RH = (temp - 25)*(0.01 + 0.00008*soRH) + RHlin  # temperature correction
        return RH
