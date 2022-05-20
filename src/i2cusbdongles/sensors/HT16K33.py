#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
I2C LED module HT16K33
"""

import time, sys
from i2cusbdongles import glob
from i2cusbdongles import util

"""
LED 8x8 module, red
28-Pin package
using: Holtek RAM Mapping 16*8 LED Controller Driver with keyscan HT16K33
Revision: V.1.10
Date: May 16, 2011
www.holtek.com
"""

class LEDHT16K33:
    """Code for the LED module HT16K33"""


    def __init__(self, HT16K33):
        self.dongle  = HT16K33["dngl"]    # "ELVdongle", "IOW-DG", "ISSdongle"
        self.addr    = HT16K33["addr"]    # 0x70 ... 0x77
        self.subtype = HT16K33["type"]    # "LED8x8" (prelim)
        self.name    = HT16K33["name"]    # HT16K33


    def HT16K33Init(self):
        """Init the LED 8x8 module"""

        # System Setup
        # The system setup register configures system operation or standby for the HT16K33.
        # The internal system oscillator is enabled when the ‘S’ bit of the system setup register is set to “1”.
        # 0b 0010 XXXS; S(write only): Turn on System oscillator (normal operation mode)
        data    = [0x21]
        rbytes  = 1
        try:
            answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="System Setup")
        except Exception as e:
            util.exceptPrint(e, sys.exc_info(), "ERROR initialzing sensor {} at dongle {}".format(self.name, self.dongle))
            util.ecprint("Is sensor connected? - Exiting")
            sys.exit()

        time.sleep(0.1)

        # Display ON and Blinking OFF
        data    = [0x80 + 0x01 + 0x00]
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Disp ON, Blink OFF")

        """
        for i in range(2):
            # Display ALL ON
            data    = [0x00 + 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,  0xff, 0xff, 0xff, 0xff, 0xff, 0xff ] #
            rbytes  = 1
            answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Disp ALL ON")

            time.sleep(0.01)

            # Display ALL OFF
            data    = [0x00 + 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ] #
            rbytes  = 1
            answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Disp ALL OFF")

            time.sleep(0.01)

        data    = [0xE0 + 0x00] # 0x00 ... 0x0f (dark ... bright)
        rbytes  = 0
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Dimming Set" + str(i))

        #sys.exit()
        """

        # ROW/INT set ( no changes seen??? assuming 0 is default)
        # The ROW/INT setup register can be set to either an LED Row output, or an INT logic output.
        # Defines INT/ROW output pin select and INT pin output active level status.
        # The ROW output is selected when the ROW/INT set register is set to “0”.
        # 0b 1010 XXAR : R=0: INT/ROW output pin is set to ROW driver output; act for ROW=X,
        data    = [0xA0 + 0x00]
        rbytes  = 1
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="ROW/INT set 0")

        for i in range(0, 16):
            data    = [0x00 + i, 255]
            rbytes  = 1
            info    = "SetPixel all"
            answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info=info, end="")
            print()

        time.sleep(0.5)

        # light up the bottom LEDs (#0) on all columns
        for i in range(0,8): self.HT16K33setPixel(i,0)


    def HT16K33setPixel(self, x, y, on = True):
        """set pixel x,y to on (OFF not yet working);  x, y from 0...7"""

        if y < 0 or y > 7 or x < 0 or x > 7:
            #print("setPixel outside range:", x, y)
            return # outside plottable range
        else:
            pass
            #print("x,y:",x,y)

        ix = int(round(x*2))
        iy = int((2**round(y))) >> 1

        if iy == 0: iy = 0x80

        if not on:
            iy = iy ^ 0xff # fails, need to know the other pics

        data    = [0x00 + ix, iy]
        rbytes  = 1
        stron   = "ON" if on else "OFF"
        info    = "SetPix {}, {:1.0f} ({})".format(x, y, stron)
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info=info, end="")
        print()


    def HT16K33setCol(self, x, y):
        """set pixel x,y to on (OFF not yet working);  x, y from 0...7"""

        ix      = round(x*2)
        iy      = 0x80
        for i in range(0, util.clamp(y, 0, 7)):
            iy += 2**i

        data    = [0x00 + ix, iy]
        rbytes  = 1
        info    = "SetCol {}, {:1.0f}".format(x, y)
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info=info, end="")
        print()


    def HT16K33runAllFunctions (self):
        """ Run all functions """

        data    = [0x80 + 0x01 + 0x00] # Display ON and Blinking OFF
        rbytes  = 0
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Display Setup Blink OFF")
        time.sleep(2)

        # Display ALL ON
        data    = [0x00 + 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,  0xff, 0xff, 0xff, 0xff, 0xff, 0x00 ]
        rbytes  = 0
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Display ALL ON")
        time.sleep(5)
        # Display Setup
        data    = [0x80 + 0x01 + 0x02] # Display ON and Blinking 2 Hz
        rbytes  = 0
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Display Setup 2 Hz")
        time.sleep(2)

        data    = [0x80 + 0x01 + 0x04] # Display ON and Blinking 1 Hz
        rbytes  = 0
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Display Setup 1 Hz")
        time.sleep(4)

        data    = [0x80 + 0x01 + 0x06] # Display ON and Blinking 0.5 Hz
        rbytes  = 0
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Display Setup 0.5 Hz")
        time.sleep(8)

        data    = [0x80 + 0x01 + 0x00] # Display ON and Blinking OFF
        rbytes  = 0
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Display Setup Blink OFF")
        time.sleep(0)

        # Dimming set
        data    = [0xE0 + 0x0f] # 0x00 ... 0x0f (dark ... bright)
        rbytes  = 0
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Dimming Set")

        a = list( (range(0,16)))
        b = list((range(16,0,-1)))
        #for x in a: print(x)
        #for x in b: print(x)
        #print(type(a))

        while True:
            for i in a + b:
                # Dimming set
                data    = [0xE0 + i] # 0x00 ... 0x0f (dark ... bright)
                rbytes  = 0
                answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Dimming Set" + str(i))
                time.sleep(0.01)
            break

        # What does this do?
        # "{X 0}: INT/ROW output pin is set to ROW driver output."
        # Row/int set to 0 presumed daefauöt for LD Matrix
        # ROW/INT set
        data    = [0xA0 + 0x01] #
        rbytes  = 0
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="ROW/INT set 1")
        time.sleep(3)
        # ROW/INT set
        data    = [0xA0 + 0x00] #
        rbytes  = 0
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="ROW/INT set 0")
        time.sleep(3)


        try:
            import numpy as np
            print("Showing sine")
            for i in range(8):
                self.HT16K33setPixel(i, round((np.sin(0.5*i) +1)*3.8))
            time.sleep(3)
        except:
            pass

        for i in range(8):
            self.HT16K33setPixel(int(i),i)

        self.HT16K33setPixel(0 , 0 )
        self.HT16K33setPixel(1 , 1 )
        self.HT16K33setPixel(2 , 2 )
        #self.HT16K33setPixel(3 , 3 , on = False)
        self.HT16K33setPixel(4 , 4 )
        self.HT16K33setPixel(5 , 5 )
        self.HT16K33setPixel(6 , 6 )
        self.HT16K33setPixel(7 , 7 )

        # Display data Address pointer
        #data    = [0x00 + 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ] # all OFF
        data    = [0x00 + 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,  0xff, 0xff, 0xff, 0xff, 0xff, 0x00 ]  # all ON
        rbytes  = 0
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Display data")

        import random

        for i in range(100):
            j = random.randint(0,16)
            i = random.randint(0,255)
            data    = [0x00 + j, i ]
            rbytes  = 0
            answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Random data")
            time.sleep(0.01)

        for j in range(0, 16, 2):
            for i in range(256):
                # Display data Address pointer
                data    = [0x00 + j, i ]
                rbytes  = 0
                answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="all data 8*256")
                time.sleep(0.002) # faster than 0.002 not possible


        # Display data
        rbytes  = 0
        data    = [0x00 + 0x00]
        for i in range(0, 50):
            data.append(i)
        answ    = self.dongle.askDongle(self.addr, data, rbytes, name=self.name, info="Display data")


        # plot a sine if numpy is available
        try:
            import numpy as np
            for i in range(8):
                self.HT16K33setPixel(i, round((np.sin(0.5*i) +1)*3.8))
                #self.HT16K33setPixel(i, round((np.sin(0.5*i) +1)*4.1))
            time.sleep(3)
        except:
            pass

        # plot a diagonal from bottom-left to top right
        for i in range(8):
            self.HT16K33setPixel(int(i),i)

        #  invert one line (invert point not working
        self.HT16K33setPixel(3 , 3 , on = False)
