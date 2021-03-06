#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
I2C module TSL2591 (Light Sensor, Visible + Infrared)
"""

import time, sys
from i2cusbdongles import glob
from i2cusbdongles import util
from i2cusbdongles.dongles.Dongle import Dongle

# Document: "TSL2591 Datasheet - Apr. 2013 - ams163.5"
# e.g.: https://www.manualshelf.com/manual/adafruit/1980/datasheet-english.html

# Sensor Bluedot:
# Herstellerreferenz: BME280 + TSL2591, ASIN: B0795WWXX8
# Light sensor: address 0x29"

#activating TSL2591 on ELVdongle +++++++++++++++++++++++++++++++++++++++++++
#ELV TSL2591 TX 14:12:43   [  9] [  9]  get ID               == b'S 52 B2 P'
#ELV         iR 14:12:43   [  9] [  9]                       == b'S 53 01 P'
#ELV TSL2591 RX 14:12:43   [  1] [  3]                       == b'50 '
#                                                            Found Sensor TSL2591

#activating TSL2591 on IOW-DG +++++++++++++++++++++++++++++++++++++++++++
#IOW TSL2591 TX 14:04:43   [  2] [  8]  get ID               == 02 C2 52 B2 00 00 00 00
#IOW         RX 14:04:43   [  1] [  8]                       == 02 02 00 00 00 00 00 00 ACK
#IOW         iR 14:04:43   [  1] [  8]                       == 03 01 53 00 00 00 00 00
#IOW         RX 14:04:43   [  1] [  8]                       == 03 01 50 00 00 00 00 00 ok, Bytes received: 6
#                                                   Answer:  == 50
#                                                            Found Sensor TSL2591

#activating TSL2591 on ISSdongle +++++++++++++++++++++++++++++++++++++++++++
#ISS TSL2591 TX 13:51:03   [  3] [  3]  get ID               == b'UR\xb2' == 55 52 B2
#ISS TSL2591 i1 13:51:03   [  1] [  4]  get ID               == b'US\xb2\x01' == 55 53 B2 01
#ISS         RX 13:51:03   [  1] [  1]                       == b'P' == 50
#                                                            Found Sensor TSL2591



class SensorTSL2591(Dongle):
    """Code for the TSL2591 sensors"""

    PID         = 0x00      # acc to document, page 16

    # CMD Register = 0b1 01 0 0000  = 0xA0 is: CMD + Normal operation
    CMD         = 0xA0

    # Gain and Integration time determine sensitivity and quality of measurement
    # Gain, doc page 6
    #         Name   Factor
    #AGAIN  = Low    1
    #AGAIN  = Med    25      1
    #AGAIN  = High   428     17.12       1
    #AGAIN  = Max    9876    395.04      23,07
    #
    # Integration time, doc page 13
    #ATIME  = 100 ms
    #ATIME  = 200 ms
    #ATIME  = 300 ms
    #ATIME  = 400 ms
    #ATIME  = 500 ms
    #ATIME  = 600 ms

    #                Name:  FieldVal,  Factor
    sensorgain  = { "Low":  (0b00,     1),
                    "Med":  (0b01,     25),
                    "High": (0b10,     428),
                    "Max":  (0b11,     9876),
                  }

    #                Name:  FieldVal,  ms
    sensorint   = { "100ms":(0b000,    100),
                    "200ms":(0b001,    200),
                    "300ms":(0b010,    300),
                    "400ms":(0b011,    400),
                    "500ms":(0b100,    500),
                    "600ms":(0b101,    600),
                  }


    def __init__(self, TSL2591):
        self.dongle  = TSL2591["dngl"]    # A dongle object "ELVdongle", "IOW-DG", "ISSdongle"
        self.addr    = TSL2591["addr"]    # 0x29
        self.subtype = TSL2591["type"]    # Device ID: 0x50
        self.name    = TSL2591["name"]    # TSL2591


    def TSL2591Init(self):
        """check ID, check PID, Reset, enable measurement"""

    # Get Device Identification = 0x50  (= as subtype)
        # ID Register (0x12) (Bit 7:0)
        data    = [self.CMD + 0x12]
        rbytes  = 1
        answ    = glob.dongles[self.dongle].askDongle(self.dongle, self.addr, data, rbytes, name=self.name, info="get ID")
        if answ[0] == self.subtype:
            util.fncprint("Found Sensor TSL2591")
        else:
            util.fecprint("Did NOT find Sensor TSL2591 - Exiting")
            sys.exit()

    # Get package identification (PID)
        # PID Register (0x11) (Bit 5:4) (2 bits only!)
        data    = [self.CMD + 0x11]
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="PID read (Bits5:4)")
        pid     = answ[0] & 0b00110000
        if pid == self.PID:
            util.fncprint("Package Identification 0b{:02b} confirmed".format(pid), color = glob.TGREEN)
        else:
            util.fecprint("Package Identification 0b{:02b} not as expected".format(pid))

    # System Reset
        # Control Register (0x01)
        #
        # Important: the System Reset will NOT return an ACK! (observed on both ELV and IOW)
        #
        data    = [self.CMD + 0x01, 0x80] # System Reset, AGAIN=00, ATIME=000
        rbytes  = 1
        #answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="System Reset")

    # Enable measurement
        # Enable Register (0x00)
        # Power the device on, enable measurements
        # Bit#0 = 1: Power ON
        # Bit#1 = 1: ALS Enable
        # Register: 0b 0000 00 11  =0x03 :
        data    = [self.CMD + 0x00, 0x03]
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Enable ALS+PON")


    def TSL2591getLumAuto(self):
        """ Function doc """

        atime    = "600ms"      # so far always use 600 ms integration time
        selector = ("Low",      # Factor = 1
                    "Med",      # Factor = 25
                    "High",     # Factor = 428
                    "Max",      # Factor = 9876
                   )
        selindex = 1            # start with Med; best chance for success in
                                # fewest cycles

        while True:
            again = selector[selindex]
            ret   = self.TSL2591getLum(gain = again, intgrl = atime)
            vis, ir, visraw, irraw, gainFct, inttime = ret

            # lower limit for autoscale must be <= min(2600, 3800, 2800)
            # chosen is 2500
            #        Name   Factor
            #                                             104
            #AGAIN = Low    1                            2600     152
            #AGAIN = Med    25      1                   65000    3800     163
            #AGAIN = High   428     17.12       1               65000    2800
            #AGAIN = Max    9876    395.04      23,07                   65000

            lastselindex = selindex
            if visraw > 65000:              # too much light
                selindex += -1              # one step down
                if selindex < 0: break      # reached the bottom?
                util.fncprint("Autodecrease Gain 1 step")

            elif visraw < 152:              # allows two step up:
                selindex += 2               # one step up
                if selindex > 3: break      # broke the ceiling?
                util.fncprint("Autoincrease Gain 2 steps")

            elif visraw < 2500:             # allows one step up
                selindex += 1               # one step up
                if selindex > 3: break      # broke the ceiling?
                util.fncprint("Autoincrease Gain 1 step")
            else:
                break                       # best value possible

        return vis, ir, visraw, irraw, gainFct, inttime


    def TSL2591getLum(self, gain = 'Low', intgrl = "100ms"):

        gainFV  = self.sensorgain[gain][0]   # Field Value
        gainFct = self.sensorgain[gain][1]   # Gain Factor

        intFV   = self.sensorint[intgrl][0]  # Field Value
        intTime = self.sensorint[intgrl][1]  # integration time in ms
        intFct  = intTime / 100              # Gain Factor by integration time

        # Control Register (0x01) - Setting Gain Mode and Integration Time
        data    = [self.CMD + 0x01, gainFV << 4 | intFV ]
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Gain:{}, Int:{} ms".format(gainFct, intTime))

        # Cycle the AEN (ALS Enable) bit in the Enable Register (truly necessary?)
        # Enable Register (0x00)
        data    = [self.CMD + 0x00, 0x01]   # ALS Disable
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Disable AEN")

        # Enable Register (0x00)
        data    = [self.CMD + 0x00, 0x03]   # ALS Enable
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Enable AEN")

        start = time.time()
        time.sleep(intTime / 1000        ) # sleeping for integration time is almost
                                           # always enough to finish conversion

        # Read the Status register until the AVALID bit (Bit #0 in Status) is set
        # Status Register (0x13)
        data    = [self.CMD + 0x13]
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="status", doPrint = True, end = "")
        if answ[0] & 0x01:
            util.ncprint("Data ready")
        else:
            util.ecprint("Data not ready", end="")
            util.ecprint(".", end="") # one dot for each call of status
            while True:
                if answ[0] & 0x01:
                    util.ncprint("ready after {:3.2f}sec".format(time.time() - start))
                    break
                data    = [self.CMD + 0x13] # Status is Register (0x13)
                rbytes  = 1
                answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="status", doPrint = False)
                util.ecprint(".", end="")

        # ALS Data Register (0x14 - 0x17)
        data    = [self.CMD + 0x14]
        rbytes  = 4
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Get data", end="")

        visraw = answ[0] | (answ[1] << 8)
        irraw  = answ[2] | (answ[3] << 8)
        util.ncprint("              Result: Vis: {}, IR: {}".format(visraw, irraw), color=glob.TDEFAULT)

        # Results are validated for being a good approximation by this
        # normalization over all Gain factors
        vis    = visraw  / gainFct / intFct
        ir     = irraw   / gainFct / intFct

        return vis, ir, visraw, irraw, gainFct, intTime


    def TSL2591runAllFunctions(self):
        """ for TSL2591 sensor """

    # Get Device Identification = 0x50  (= as subtype)
        # ID Register (0x12) (Bit 7:0)
        data    = [self.CMD + 0x12]
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="get ID")
        if answ[0] == self.subtype:
            util.fncprint("Found Sensor TSL2591")
        else:
            util.fecprint("Did NOT find Sensor TSL2591 - Exiting")
            sys.exit()

    # Get package identification (PID)
        # PID Register (0x11) (Bit 5:4) (2 bits only!)
        data    = [self.CMD + 0x11]
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="PID read (B5:4)")
        pid     = answ[0] & 0b00110000
        if pid == self.PID:
            util.fncprint("Package Identification '0b{:02b}' confirmed".format(pid), color = glob.TGREEN)
        else:
            util.fecprint("Package Identification '0b{:02b}' not as expected".format(pid))

    # System Reset
        # Control Register (0x01)
        # Important: the System Reset will NOT return an ACK! (observed on both ELV and IOW)
        data    = [self.CMD + 0x01, 0x80] # System Reset, AGAIN=00, ATIME=000
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="System Reset")

    # Enable measurement
        # Enable Register (0x00)
        # Power the device on, enable measurements
        # Bit#0 = 1: Power ON
        # Bit#1 = 1: ALS Enable
        # Register: 0b 0000 00 11  =0x03 :
        data    = [self.CMD + 0x00, 0x03]
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Enable ALS+PON")

    # Get status
        # Status Register (0x13)
        data    = [self.CMD + 0x13]
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="status")

    # Get data
        # ALS Data Register (0x14 - 0x17)
        data    = [self.CMD + 0x14]
        rbytes  = 4
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="data")
        util.fncprint("Data:", answ)

    # Set Med gain
        # Control Register (0x01)
        data    = [self.CMD + 0x01, 0x10]
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Med gain")

    # Set High gain
        # Control Register (0x01)
        data    = [self.CMD + 0x01, 0x20]
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="High gain")

    # Set High gain + 300 ms integration
        # Control Register (0x01)
        data    = [self.CMD + 0x01, 0x22]
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="High gain+300ms")

    # Set Med gain + 300 ms integration
        # Control Register (0x01)
        data    = [self.CMD + 0x01, 0x12]
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Med gain+300ms")

    # Set Med gain + 600 ms integration
        # Control Register (0x01)
        data    = [self.CMD + 0x01, 0x15]
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Med gain+600ms")

    def close(self):
        
        pass