#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
SCD40/SCD41 CO2/Temp/RH sensor
"""

import sys, time

from i2cusbdongles import glob
from i2cusbdongles import util

"""
SCD4x
https://sensirion.com/products/catalog/SCD41/
"""


class SensorSCD4x:
    """Code for the SCD40/SCD41 sensors"""
    
    min_cycle = 5 # minimum time (in sec) between 2 measurements
    
    commands = {
                'start_periodic_measurement': {'code':0x21b1, 'type':'send', 'rbytes':0, 'wait_ms':0,'during_meas':False},
                'read_measurement': {'code':0xec05, 'type':'read', 'rbytes':9, 'wait_ms':1,'during_meas':True},
                'stop_periodic_measurement': {'code':0x3f86, 'type':'send', 'rbytes':0, 'wait_ms':500,'during_meas':True},
                'set_temperature_offset': {'code':0x241d, 'type':'write', 'rbytes':0, 'wait_ms':1,'during_meas':False},
                'get_temperature_offset': {'code':0x2318, 'type':'read', 'rbytes':3, 'wait_ms':1,'during_meas':False},
                'set_sensor_altitude': {'code':0x2427, 'type':'write', 'rbytes':0, 'wait_ms':1,'during_meas':False},
                'get_sensor_altitude': {'code':0x2322, 'type':'read', 'rbytes':3, 'wait_ms':1,'during_meas':False},
                'set_ambient_pressure': {'code':0xe000, 'type':'write', 'rbytes':0, 'wait_ms':1,'during_meas':True},
                'perform_forced_recalibration': {'code':0x362f, 'type':'send_fetch', 'rbytes':3, 'wait_ms':400,'during_meas':False},
                'set_automatic_self_calibration_enabled': {'code':0x2416, 'type':'write', 'rbytes':0, 'wait_ms':1,'during_meas':False},
                'get_automatic_self_calibration_enabled': {'code':0x2313, 'type':'read', 'rbytes':3, 'wait_ms':1,'during_meas':False},
                'start_low_power_periodic_measurement': {'code':0x21ac, 'type':'send', 'rbytes':0, 'wait_ms':0,'during_meas':False},
                'get_data_ready_status': {'code':0xe4b8, 'type':'read', 'rbytes':3, 'wait_ms':1,'during_meas':True},
                'persist_settings': {'code':0x3615, 'type':'send', 'rbytes':0, 'wait_ms':800,'during_meas':False},
                'get_serial_number': {'code':0x3682, 'type':'read', 'rbytes':9, 'wait_ms':1,'during_meas':False},
                'perform_self_test': {'code':0x3639, 'type':'read', 'rbytes':3, 'wait_ms':10000,'during_meas':False},
                'perform_factory_reset': {'code':0x3632, 'type':'send', 'rbytes':0, 'wait_ms':1200,'during_meas':False},
                'reinit': {'code':0x3646, 'type':'send', 'rbytes':0, 'wait_ms':20,'during_meas':False},
                'measure_single_shot': {'code':0x219d, 'type':'send', 'rbytes':0, 'wait_ms':5000,'during_meas':False},
                'measure_single_shot_rht_only': {'code':0x2196, 'type':'send', 'rbytes':0, 'wait_ms':50,'during_meas':False},
                }

    def __init__(self, SCD4x):
        self.dongle  = SCD4x["dngl"]    # "ELVdongle", "IOW-DG", "ISSdongle"
        self.addr    = SCD4x["addr"]    # addr:0x48 ... 0x4F
        self.subtype = SCD4x["type"]    # "LM75" or "LM75B"
        self.name    = SCD4x["name"]    # "LM75"
        self.last_time = None
#
#    def __split_2_bytes__(self, integer, order='big'):
#        
#        order = [1,0] if order == 'big' else [0,1]        
#        return [integer >> (8*i) & 0xff for i in order]

    @property
    def SCD4xready(self):
        if (time.time() - self.last_time()) > self.min_cycle:
            if self.SCD4xGetDataReady():
                return True
        return False
        

    def __CRC__(self, data):
        """
        calculates 8-Bit checksum with given polynomial
        """       
        crc = 0xff
        for current_byte in data:
            crc = (crc ^ current_byte) & 0xff
            
            for crc_bit in range(8,0,-1):   
                if (crc & 0x80):
                    crc = ((crc << 1) & 0xff) ^ (0x31)
                else:
                    crc = (crc << 1) & 0xff

        return crc
         

    def __I2Ccommand__(self, command_name, set_value=None, info=""):
        """General method for sending an I2C command to the SCD4x sensor"""
        command = self.commands[command_name]
        data = list(command['code'].to_bytes(2, 'big'))
        if command['type'] in ['write', 'send_fetch']:
            if set_value is not None:
                set_bytes = list(int(set_value).to_bytes(2, 'big'))
                data += set_bytes
                data += [self.__CRC__(set_bytes)]
            else:
                data += [self.__CRC__(data)]
        try:
            answ = self.dongle.askDongle(self.addr, data, command['rbytes'], wait_time=command['wait_ms'], name=self.name, info=info)
        except Exception as e:
            util.exceptPrint(e, sys.exc_info(), "ERROR when '{}' (sensor {}, dongle {})".format(command_name, self.name, self.dongle))
            util.ecprint("Is sensor connected? - Exiting")
            sys.exit()
        return answ

    def close(self):
        """Action to do when the util.shutdown() function is called """
        
        self.SCD4xStopMeas()
        

    def SCD4xgetAll(self):
        """ Read all measurements """

        answ = self.__I2Ccommand__('read_measurement', info='Get All')
        
        self.last_time = time.time()
        
        CO2 = (answ[0]<<8) + answ[1] #TODO: always return 0 ??
        CO2_CRC = answ[2]
        T = -45 + 175*((answ[3]<<8) + answ[4])/(2**16)
        T_CRC = answ[5]
        RH = 100*((answ[6]<<8) + answ[7])/(2**16)
        RH_CRC = answ[8]

        util.ncprint(" "*23+"Result: CO2={:d}, RH={:2.1f}, T={:3.2f}".format(CO2,RH,T), color=glob.TDEFAULT)

        return CO2, T, RH     
            

    def SCD4xInit(self, autostart=True):
        """Asks anything to the sensor to check initialization"""
        answ = self.SCD4xGetSerialNumber()
        util.ncprint(" "*23+"S/N = "+str(answ))
        
        self.SCD4XPerformSelfTest()
        
        if autostart:
            self.SCD4xStartMeas()

    def SCD4xGetSerialNumber(self):
        """Asks serial number"""
        answ = self.__I2Ccommand__('get_serial_number', info='Get S/N')
        sn = answ[0]<<32|answ[1]<<16|answ[2]
        return sn


    def SCD4xGetDataReady(self):
        """Asks sensor if new data is available"""
        answ = self.__I2Ccommand__('get_data_ready_status', info='Is data ready?')
        
        #If the least significant 11 bits of word[0] are 0 → data not ready else → data ready for read-out
        if answ[0]+answ[1]+(answ[2]&0x07) == 0:
            util.ecprint("Data not ready")
            return False
        else:
            return True
        
    def SCD4xStartMeas(self):
        """Asks to start a periodic measurement"""
        self.__I2Ccommand__('start_periodic_measurement', info='Start meas.')
        self.last_time = time.time()

    def SCD4xStopMeas(self):
        """Returns the sensor to idle state"""
        self.__I2Ccommand__('stop_periodic_measurement', info='Stop meas.')

    def SCD4xFactoryReset(self):
        """
        The perform_factory_reset command resets all configuration settings stored
        in the EEPROM and erases the FRC and ASC algorithm history.
        """
        self.__I2Ccommand__('perform_factory_reset', info='factory reset')

    def SCD4xReInit(self):
        """
        The reinit command reinitializes the sensor by reloading user settings from EEPROM.
        Before sending the reinit command, the stop measurement command must be issued.
        If the reinit command does not trigger the desired re-initialization,
        a power-cycle should be applied to the SCD4x.
        """
        self.__I2Ccommand__('reinit', info='SCD4x reinit')
        time.sleep(1) #1000 ms required after soft restart

    
    def SCD4xSetSensorAltitude(self, altitude=0):
        """
        Reading and writing of the sensor altitude must be done while the SCD4x is in idle mode.
        Typically, the sensor altitude is set once after device installation.
        To save the setting to the EEPROM, the persist setting command must be issued.
        Per default, the sensor altitude is set to 0 meter above sea-level.
        """
        self.__I2Ccommand__('set_sensor_altitude', set_value=altitude, info='Set SCD4x altitude')

    def SCD4xGetSensorAltitude(self):
        
        answ = self.__I2Ccommand__('get_sensor_altitude', info='Get SCD4x altitude')
        
        #altitude = (answ[0]<<16)|(answ[1]<<8)|(answ[2]<<0)
        altitude_bytes = [answ[0],answ[1]]
        altitude_crc = answ[2]
        altitude = int.from_bytes(altitude_bytes,'big')
        
        return altitude

    def SCD4xSetAmbiantPressure(self, pressure=0):
        """
        The set_ambient_pressure command can be sent during periodic measurements to enable continuous pressure compensation.
        Note that setting an ambient pressure using set_ambient_pressure overrides any pressure compensation based on a previously set sensor altitude.
        """
        self.__I2Ccommand__('set_ambient_pressure', set_value=pressure, info='Set SCD4x pressure')


    def SCD4XPerformSelfTest(self):
        
        answ = self.__I2Ccommand__('perform_self_test', info='SCD4x self-test')
        check_bytes = [answ[0],answ[1]]
        check_crc = answ[2]
        check = int.from_bytes(check_bytes,'big')
        if check_crc != self.__CRC__(check_bytes):
            print('CRC failed for autotest - please try again')
        else:
            if check == 0:
                print('SCD4x sensor is OK :-)')
            else:
                print('SCD4x sensor malfunction detected')
            
            
    def SCD4xPerformForcedRecalibration(self, ref_ppm=400, silent=False):
        """
        Perform a forced recalibration by giving the sensor a reference CO2 level
        """
        if not silent:
            r = input("/!\ Calibration will block the current thread during 3 min. Continue anyway? (y/n):")
            if not r.strip().lower().startswith('y'): return
        
        if self.SCD4xGetDataReady():
            was_running = True
            self.SCD4xStopMeas()
        else:
            was_running = False
            
        self.SCD4xStartMeas()
        print("Acquiring data for 3 min before calibration")
        time.sleep(3*60)
        self.SCD4xStopMeas()
        print("Forcing calibration with reference CO2 level of {:.0f}ppm".format(ref_ppm))
        answ = self.__I2Ccommand__('perform_forced_recalibration', set_value=ref_ppm, info='Forced calibr.')
        cal_bytes = [answ[0],answ[1]]
        CRC = answ[2]
        FRC = int.from_bytes(cal_bytes,'big')
        if FRC == 0xff:
            print("Calibration has failed - please try again")
        elif CRC != self.__CRC__(cal_bytes):
            print("Calibration CRC is incorrect - please try again")
        else:
            FRC = FRC - 0x8000
            print("Calibration succeded! CO2 offset is {:.0f}ppm".format(FRC))            
            
        if was_running: self.SCD4xStartMeas()
        return FRC
        
        