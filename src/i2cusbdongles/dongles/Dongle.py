#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Code for a Generic Dongle
"""

class Dongle:
    """Code for a genereic Dongle"""

    name        = "Genericdongle"
    short       = "dongle"

    def __init__(self):
        """Initializes the dongle"""
        return None


    def askDongle(self, addr, data, rbytes, wait_time=0, name="no name", info="no info", doPrint=True, end="\n"):
        """ Asks th dongle to send or read data to/from the sensor """

        return NotImplemented


    def close(self):
        """ Closes the dongle """

        print(self.name + " is closed")

