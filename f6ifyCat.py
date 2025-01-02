# v1.5 P. Nouchi le 23 Decembre 2024
import math
import sys
import time

import pygame
import pygame.time

import argparse
import configparser
import os
import pygame.midi
import serial
from serial import SerialException

# class PyCom:
#     def __init__(self, debug: bool = False):
#         self._ser = serial.Serial('com1')
#         self._debug = debug
#         if self._debug:
#             print(self._ser.name)
#             print(self._ser.baudrate)
#
#     def _send_command(self, command, data=b'', preamble=b'') -> tuple[int, int, bytes]:
#
#         self._ser.write(preamble + b'\xfe\xfe\x48\xe0' + command + data + b'\xfd')
#
#         # Our cable reads what we send, so we have to remove this from the buffer first
#         self._ser.read_until(expected=b'\xfd')
#
#         # Now we are reading replies
#         reply = self._ser.read_until(expected=b'\xfd')
#
#         return reply
#
#     def power_on(self):
#         wakeup_preamble_count = 8
#         if self._ser.baudrate == 19200:
#             wakeup_preamble_count = 27
#         elif self._ser.baudrate == 9600:
#             wakeup_preamble_count = 14
#
#         self._send_command(b'\x18\x01', preamble=b'\xfe' * wakeup_preamble_count)
#
#     def power_off(self):
#         self._send_command(b'\x18\x00')
#
#     def read_transceiver_id(self):
#         reply = self._send_command(b'\x19\x00')
#         return reply
#
#     def read_operating_frequency(self):
#         reply = self._send_command(b'\x03')
#         return reply
#
#     def read_operating_mode(self):
#         reply = self._send_command(b'\x04')
#         return reply
#
#     def send_operating_frequency(self, frequency: float):
#         reply = self._send_command(b'\x03')
#         return reply
#
#     def read_operating_mode(self):
#         reply = self._send_command(b'\x04')
#         return reply
#
#     def read_squelch_status(self):
#         reply = self._send_command(b'\x15\x01')
#         return reply
#
#     def read_squelch_status2(self):
#         reply = self._send_command(b'\x15\x05')
#         return reply
# import enum
from enum import Enum

class MODE(Enum):
    LSB = 1
    USB = 2
    CW = 3
    FM = 4
    AM = 5
    DIGL = 6
    DIGU = 9


WT_DJ_JOGORPOT  = 176
WT_DJ_JOGA = 48
WT_DJ_SHIFTJOGA = 55
WT_DJ_JOGB = 49
WT_DJ_SHIFTJOGB = 56
# *** Potentiometres ***
WT_DJ_POTVOLUMEA = 57
WT_DJ_POTVOLUMEB = 61
WT_DJ_POTMEDIUMA = 59
WT_DJ_POTMEDIUMB = 63
WT_DJ_POTBASSA = 60
WT_DJ_POTBASSB = 64
#*** Cross-Fader ***
WT_DJ_CROSSFADER = 54
#*** Buttons ***
WT_DJ_PUSH_BUTTON = 144
WT_DJ_BTN_SYNC_A = 35
WT_DJ_BTN_CUE_A = 34
WT_DJ_BTN_PLAY_A = 33
WT_DJ_BTN_SYNC_B = 83
WT_DJ_BTN_CUE_B = 82
WT_DJ_BTN_PLAY_B = 81
WT_DJ_BTN_1A = 1
WT_DJ_BTN_SHIFT1A = 5
WT_DJ_BTN_2A = 2
WT_DJ_BTN_3A = 3
WT_DJ_BTN_4A = 4
WT_DJ_BTN_1B = 49
WT_DJ_BTN_2B = 50
WT_DJ_BTN_3B = 51
WT_DJ_BTN_4B = 52
WT_DJ_BTN_SHIFT1B = 53
WT_DJ_BTN_SHIFT2B = 54
WT_DJ_BTN_SHIFT3B = 55
WT_DJ_BTN_SHIFT4B = 56
WT_DJ_BTN_REC = 43
WT_DJ_BTN_SHIFTREC = 44
WT_DJ_BTN_AUTOMIX = 45
WT_DJ_BTN_SHIFTAUTOMIX = 46
WT_DJ_BTN_MODE = 48
WT_DJ_BTN_SHIFT = 47

VFO_A = 0
VFO_B = 1
FOOTSWITCH = 10
DJCONTROL = 0

Config = configparser.ConfigParser(allow_no_value=True)  # allow_no_value=True -> to allow adding comments without value, so no trailing =

###########################################
# all backlights on Midi console
###########################################
def ledsON(midi_out):
    midi_out.write([[[144, 1, 127], 0], [[144, 2, 127], 0], [[144, 3, 127], 0], [[144, 4, 127], 0], [[144, 33, 127], 0],
                    [[144, 34, 127], 0], [[144, 35, 127], 0], [[144, 49, 127], 0], [[144, 50, 127], 0],
                    [[144, 51, 127], 0], [[144, 52, 127], 0], [[144, 81, 127], 0], [[144, 82, 127], 0],
                    [[144, 83, 127], 0], [[144, 43, 127], 0], [[144, 45, 127], 0], [[144, 48, 127], 0]])


###########################################
# all backlights on Midi console
###########################################
def ledsOFF(midi_out):
    midi_out.write(
        [[[144, 1, 0], 0], [[144, 2, 0], 0], [[144, 3, 0], 0], [[144, 4, 0], 0], [[144, 33, 0], 0], [[144, 34, 0], 0],
         [[144, 35, 0], 0], [[144, 49, 0], 0], [[144, 50, 0], 0], [[144, 51, 0], 0], [[144, 52, 0], 0],
         [[144, 81, 0], 0], [[144, 82, 0], 0], [[144, 83, 0], 0], [[144, 43, 0], 0], [[144, 45, 0], 0],
         [[144, 48, 0], 0]])


###########################################
# all backlights on Midi console
###########################################
def blinkLED(numTimes, speed, midi_out):
    for i in range(0, numTimes):  ## Run loop numTimes
        ledsON(midi_out)
        time.sleep(speed)
        ledsOFF(midi_out)
        time.sleep(speed)

########################################
# Read the ini file and get settings
# datas are strings so need to be converted !
########################################
def ReadIniFile():
    try:
        # declare global variables
        global radioModel
        global trxAddress
        global radioSpeed
        global radioPort
        global radioBits
        global radioStop
        global radioParity
        global radioXonXoff
        global radioRtsCts
        global radioDsrDtr
        global midiDeviceIn
        global midiDeviceOut
        global radioDefaultMode
        global radioDefaultVFO
        # global RadioFiltre
        global radioMode
        global debug
        global kenwood
        global newIcom
        global RohdesShwartz
        global yaesu
        global flex
        global noAction
        global preamble
        global postamble
        global trxAddress
        global icomRITValue
        global RITStep
        global vfo
        global ritFreq
        global launched

        # read ini file
        Config.read('midi2Cat.ini')

        # check if Midi section exists
        if Config.has_section('Midi'):
            midiDeviceIn = Config.getint('Midi', 'deviceIN')  # get the device Midi IN, reads and converts in INT
            midiDeviceOut = Config.getint('Midi', 'deviceOUT')  # get the device Midi OUT
        else:
            print("Midi section missing in config file. Please correct this !")
            sys.exit(1)

        # check if default section exists
        if Config.has_section('Default'):
            radioDefaultMode = Config.get('Default', 'mode')
            radioDefaultVFO = Config.get('Default', 'VFO')
            vfoStep = int(Config.get('Default', 'vfoStep'))
            vfo = radioDefaultVFO
            print("vfoStep is", vfoStep)
        else:
            print("Default section missing in config file. Please correct this !")
            sys.exit(1)

        # check if Radio section exists
        if Config.has_section('Radio'):
            radioModel = Config.get('Radio', 'model')
            if radioModel == 'ic706':
                preamble = b'\xfe\xfe\x48\xe0'
                yaesu = False
                kenwood = False
                trxAddress = b'\x48'
                flex = False
            elif radioModel == 'ic756pro3':
                preamble = b'\xfe\xfe\x6e\xe0'
                yaesu = False
                kenwood = False
                trxAddress = b"\x6e"
                flex = False
            elif radioModel == 'ic7610':
                yaesu = False
                preamble = b"\xFE\xFE\x98\xE0"  # ic7610
                trxAddress = b"\x98"
                kenwood = False
                newIcom = False
                flex = False
            elif radioModel == 'ts590':
                trxAddress = b"\x00"
                yaesu = False
                kenwood = True
                newIcom = False
                flex = False
            elif radioModel == "kenwood":
                trxAddress = b"\x00"
                yaesu = False
                kenwood = True
                newIcom = False
                flex = False
            elif radioModel == "SDRConsole":
                trxAddress = b"\x00"
                yaesu = False
                kenwood = True
                newIcom = False
                flex = False
            elif radioModel == "RohdesShwartz":
                trxAddress = b"\x00"
                yaesu = False
                RohdesShwartz = True
                newIcom = False
                flex = False
            elif radioModel == "Yaesu":
                trxAddress = b"\x00"
                yaesu = True
                kenwood = True
                newIcom = False
                flex = False
                RohdesShwartz = False
            elif radioModel == "Flex":
                trxAddress = b"\x00"
                flex = True
                yaesu = False
                kenwood = False
                newIcom = False

            radioPort = Config.get('Radio', 'comport')
            radioSpeed = Config.getint('Radio', 'speed')  # reads and converts in INT
            radioBits = Config.getint('Radio', 'bits')
            radioStop = Config.getint('Radio', 'stop')
            radioParity = Config.get('Radio', 'parity')
            radioXonXoff = Config.getint('Radio', 'xonxoff')
            radioRtsCts = Config.getint('Radio', 'rtscts')
            radioDsrDtr = Config.getint('Radio', 'dsrdtr')
            print("Radio model", radioModel, "Comport=", radioPort, "Speed=", radioSpeed, "Bits=", radioBits, "Stop=",
                  radioStop, "Parity=", radioParity)
        else:
            print("Radio section missing in config file. Please correct this !")
            sys.exit(1)

        # check if Commands section exists
        if Config.has_section('Commands'):
            # print ("Commands section OK")
            # extraction des commandes avec la commande .partition('.')
            debug = Config.getint('Commands', 'debug')
            print('debug Value is %d' % debug)
        else:
            print("Commands section missing in config file. Please correct this !")
            sys.exit(1)

    # if an option is missing, raise an error
    except configparser.NoOptionError:
        print(
            "Missing option(s) in config file !\nPlease correct this or remove file to allow creating a default one !")
        sys.exit(1)


    except configparser.NoSectionError:
        print(
            "Missing section(s) in config file !\nPlease correct this or remove file to allow creating a default one !")
        sys.exit(1)


#####################################
# init the Midi device
#####################################
def InitMidiDevice(midiDeviceIn):
    pygame.midi.init()

    # testing if device is already opened
    if pygame.midi.get_device_info(midiDeviceIn)[4] == 1:
        print('Error: Can''t open the MIDI device - It''s already opened!')
        sys.exit(1)

    # testing if input device is an input
    if pygame.midi.get_device_info(midiDeviceIn)[3] == 1:
        print('Error: Midi input device selected in not an input ! Please correct this.')
        sys.exit(1)

    # testing if input device is an input
    if pygame.midi.get_device_info(midiDeviceOut)[3] == 0:
        print('Error: Midi output device selected in not an output ! Please correct this')
        sys.exit(1)

        # count the number of Midi devices connected
    MidiDeviceCount = pygame.midi.get_count()
    print("Number of Midi devices found =", MidiDeviceCount)

    # display the default Midi device
    print("\nWindows default Midi input device =", pygame.midi.get_default_input_id())
    print("Windows default Midi output device =", pygame.midi.get_default_output_id())

    # display Midi device selected by config file
    print("\nConfig file selected Midi INPUT device =", midiDeviceIn)
    print("Config file selected Midi OUTPUT device =", midiDeviceOut)

    # display infos about the selected Midi device
    print("\nInfos about Midi devices :")
    for n in range(pygame.midi.get_count()):
        print(n, pygame.midi.get_device_info(n))

    # open Midi device
    # my_input = pygame.midi.Input(midiDeviceIn)


########################################
# create_midi2Cat_inifile
# in case the ini file does not exist, create one with default values
########################################
def CreateIniFile():
    inifile = open("midi2Cat.ini", 'w')

    # add default section
    Config.add_section('Default')
    Config.set('Default', '# midi2Cat config file')
    Config.set('Default', '# defaults values created by program')
    Config.set('Default', 'mode', 'USB')
    Config.set('Default', 'VFO', 'A')
    # add section Midi
    Config.add_section('Midi')
    # add settings
    Config.set('Midi', 'deviceIN', '1')
    Config.set('Midi', 'deviceOUT', '3')

    # add section Radio
    Config.add_section('Radio')
    # add settings
    Config.set('Radio', 'model', 'ts590')
    Config.set('Radio', 'comport', 'COM2')
    Config.set('Radio', 'speed', '115200')
    Config.set('Radio', 'bits', '8')
    Config.set('Radio', 'stop', '1')
    Config.set('Radio', 'parity', 'N')
    Config.set('Radio', 'xonxoff', '0')
    Config.set('Radio', 'rtscts', '0')
    Config.set('Radio', 'dsrdtr', '0')

    # add section Commands
    Config.add_section('Commands')
    # add settings
    Config.set('Commands', 'debug', 0)
    Config.set('Commands', '14412', 'TS0;')
    Config.set('Commands', '144.3', 'FR0;FT1;')

    # and lets write it out...
    Config.write(inifile)
    inifile.close()

    # now read the config file
    ReadIniFile()


########################################
# send data to radio
########################################
def SendToRadio(strCat):
    radioSer.write(strCat.encode())

#################################
# Increment or Decrement the VFO of Icom TRX
#################################
def DownIcom(radioSer, vfoStep):
    frequency = 0
    while frequency == 0 or frequency is None:
        try:
            frequency = update_freqIcom()
        except:
            frequency = 0
        if frequency < 1800000:
            frequency = 0
    if debug >= 2: print("Down VFO by %d" % vfoStep)
    fToSend = frequency - vfoStep
    setFrequency(radioSer, fToSend)


def UpIcom(radioSer, vfoStep):
    frequency = 0.0
    while frequency == 0.0 or frequency is None:
        frequency = update_freqIcom()
        if frequency < 1800000:
            frequency = 0
    if debug >= 2: print("Up VFO by %d" % vfoStep)
    fToSend = frequency + vfoStep
    setFrequency(radioSer, fToSend)


def bcd4(d1, d2, d3, d4):
    out = b''
    first = bytes([(16 * d1) + d2])
    second = bytes([(16 * d3) + d4])
    # return 16 * d1 + d2, 16 * d3 + d4
    out = out.join([first, second])
    return out


# pack 2 BCD digits
def bcd2(d1, d2):
    out = b''
    only = bytes([(16 * d1) + d2])
    out = out.join([only])
    return out


def setFrequency(radioSer, freq):
    fs = "%010d" % freq
    out = b''
    out1 = bcd4(int(fs[8]), int(fs[9]), int(fs[6]), int(fs[7]))
    out2 = bcd4(int(fs[4]), int(fs[5]), int(fs[2]), int(fs[3]))
    out3 = b'\x00'  # 'bcd2(int(fs[0]), int(fs[1]))
    out = out.join([out1, out2, out3])

    strCattoSend = b''
    strCattoSend = strCattoSend.join([preamble, b"\x05", out, b'\xfd'])
    if debug >= 2: print(strCattoSend)
    radioSer.write(strCattoSend)
    # echo = radioSer.read(6)
    # if debug >= 2: print(f"got reply of {len(echo):d} chars")


def update_freqIcom(*args):
    f = 0.0
    strCat = preamble + (b"\x03\xfd")
    radioSer.write(strCat)
    header = b"\xfe\xfe" + trxAddress + b"\xe0\x03\xfd\xfe\xfe\xe0" + trxAddress
    #result = b""
    #countSDR = 0
    s = b''
    byte_freq = b''
    str_freq = ''
    big_endian_bytes = b''
    result = radioSer.read(17)
    #if result[16] == b'\xfd':
    byte_freq = result[11:16]
    big_endian_bytes = byte_freq[::-1]
    str_freq = big_endian_bytes.hex()
    f = int(str_freq) / 1000
    return f


def update_freq(*args):
    if flex:
        strCat = 'ZZFA;'
        header = "ZZFA"
    elif kenwood:
        strCat = 'FA;'  # ask the frequency
        header = "FA"
    radioSer.write(strCat.encode())
    lineSDR = ""
    s = ""
    while s != ";":
        s = radioSer.read().decode("utf-8")
        lineSDR += s

    if flex:
        freq = lineSDR[0:4]
        rx_freq = lineSDR[4:15]
    else:
        freq = lineSDR[0:2]
        rx_freq = lineSDR[2:13]

    if freq == header:
        f = int(rx_freq)
        fa = f / 1000
        strFreq = str("A: %6.3f" % fa)
        if debug == 2: print(strFreq)
    else:
        f = 0
    return f
def update_freqB(*args):
    if flex:
        strCat = 'ZZFB;'
        header = "ZZFB"
    elif kenwood:
        strCat = 'FB;'  # ask the frequency
        header = "FB"
    radioSer.write(strCat.encode())
    lineSDR = ""
    s = ""
    while s != ";":
        s = radioSer.read().decode("utf-8")
        lineSDR += s

    if flex:
        freq = lineSDR[0:4]
        rx_freq = lineSDR[4:15]
    else:
        freq = lineSDR[0:2]
        rx_freq = lineSDR[2:13]

    if freq == header:
        f = int(rx_freq)
        fa = f / 1000
        strFreq = str("B: %6.3f" % fa)
        if debug == 2: print(strFreq)
    else:
        f = 0
    print("Frequence is ", f) 
    return f

def read_power(*args):
    if flex:
        strCat = 'ZZPC;'
        header = 'ZZPC'
    else:
        strCat = 'PC;'
        header = 'PC'
    radioSer.write(strCat.encode())
    lineSDR = ""
    s = ""
    while s != ";":
        s = radioSer.read().decode("utf-8")
        lineSDR += s

    if flex:
        rxPwr = lineSDR[4:6]
        pwr = lineSDR[4:7]
    else:
        rxPwr = lineSDR[0:2]
        pwr = lineSDR[2:4] + "," + lineSDR[4]
    if rxPwr == header:
        rx_power = pwr
        if debug == 2: print("Power is " + rx_power)
    else:
        rx_power = ""
    return rx_power

def read_nb(*arg):
    strCat = 'NB;'
    header = 'NB'
    radioSer.write(strCat.encode())
    lineSDR = ""
    s = ""
    while s != ";":
        s = radioSer.read().decode("utf-8")
        lineSDR += s
    rxNB = lineSDR[0:2]
    nb = lineSDR[2]
    if rxNB == header:
        nb = lineSDR[2]
    if debug == 2: print("NB is " + nb)
    else:
        rxNB = ""
    return nb
    
def read_nr(*arg):
    strCat = 'NR;'
    header = 'NR'
    radioSer.write(strCat.encode())
    lineSDR = ""
    s = ""
    while s != ";":
        s = radioSer.read().decode("utf-8")
        lineSDR += s
    rxNR = lineSDR[0:2]
    nr = lineSDR[2]
    if rxNR == header:
        nr = lineSDR[2]
    if debug == 2: print("NR is " + nr)
    else:
        rxNR = ""
    return nr

"""def update_freqB(*args):
    f = 0
    if kenwood:
        strCat = 'FB;'      # ask the frequency
        radioSer.write(strCat.encode())
        lineSDR = ""
        s = ""
        while s != ";":
            s = radioSer.read().decode("utf-8")
            lineSDR += s

        if lineSDR[0:2] == 'FB':
            # print(lineSDR)
            rx_freqB = lineSDR[3:13]
            f = int(rx_freqB)
            fb = f / 1000
            strFreqB = str("B: %6.3f" % fb)
            if debug == 2: print(strFreqB)
    else:
        strCat = preamble + (b"\x03\xfd")
        radioSer.write(strCat)
        headerfromCIV = b"\xfe\xfe\x00" + trxAddress
        headerfromTRX = b"\xfe\xfe\xe0" + trxAddress
        lineSDR = b""
        countSDR = 0
        s = b""
        result = ""
        while countSDR < 10:
            s = radioSer.read()
            lineSDR += s
            countSDR = len(lineSDR)
            if s != b"":
                result += str("%02x" % ord(s))
            if s == b"\xFD":
                lineSDR = b""
                result = ""

        if (lineSDR[0:4] == headerfromCIV or lineSDR[0:4] == headerfromTRX) and len(result) > 16:
            f = 0
            fr = []
            res = 0
            for k in [8, 9, 6, 7, 4, 5, 2, 3]:
                res = int(result[k + 8])
                fr.append(res)

            f = fr[0] * 10000000 + fr[1] * 1000000 + fr[2] * 100000 + fr[3] * 10000 + fr[4] * 1000 + fr[5] * 100 + \
                fr[6] * 10 + fr[7]
            # rx_freq = lineSDR[5:11]
            # f = int(rx_freq)
    return f
"""
def SetFrequencykenwood(dwFrequency, vfo):
    if yaesu == True:
        f = str("%09d" % dwFrequency)
    else:
        f = str("%011d" % dwFrequency)
    if flex:
        strCat= 'ZZFA' + f + ';'
    else:
        strCat = 'F' + vfo + f + ';'
    if debug >= 1:
        print('Command Sent is ' + strCat)
    SendToRadio(strCat)


def GetfreqKenwood(vfo):
    freq = 0
    if vfo == 'A':
        pass # freq = float(var_freqA.get())
    else:
        pass #  freq = float(var_freqB.get())
        return freq
################################
# Increment or Decrement the VFO of kenwood TRX
#################################
def UpKenwood(vfoStep, vfo):
    if vfo == 'A':
        f = update_freq()
    else:
        f = update_freqB()
    f += vfoStep
    SetFrequencykenwood(f, vfo)


def DownKenwood(vfoStep, vfo):
    if vfo == 'A':
        f = update_freq()
    else:
        f = update_freqB()

    f -= vfoStep
    SetFrequencykenwood(f, vfo)

def GetMode(*args):
    mode = ""
    if flex:
        strCat = 'ZZMD;'
        header = 'ZZMD'
    else:
        strCat = 'MD;'
        header = 'MD'
    radioSer.write(strCat.encode())
    lineSDR = ""
    s = ""
    while s != ";":
        s = radioSer.read().decode("utf-8")
        lineSDR += s
    if flex:
        rx = lineSDR[0:4]
        rx_mode = lineSDR[4:6]
    else:
        rx = lineSDR[0:2]
        rx_mode = lineSDR[2]

    if debug == 2: print("mode is " + MODE(int(rx_mode)))
    if rx == header:
        if rx_mode == '7':
            mode = "CW"
        elif rx_mode == '1':
            mode = 'LSB'
        elif rx_mode == '2':
            mode = "USB"
        elif rx_mode == '3':
            mode = 'CW'
        elif rx_mode == '4':
            mode = 'FM'
        elif rx_mode == '5':
            mode = 'AM'
        elif rx_mode == '6':
            mode = 'DIGL'
        elif rx_mode == '9':
            mode = "DIGU"
        else: mode = ""
    else: mode = "Can't Read" 
    # return MODE(int(rx_mode))
    return rx_mode
########################################
# start of program
########################################
global vfoStep
global pwrStr
mode_Flex = {"00":"LSB", "01":"USB", "03":"CW-L", "04":"CW-U", "05":"FM", "06":"AM", 
             "07":"DIGI-U", "09":"DIGI-L", "10":"SAM", "11":"NFM", "12":"DFM", 
             "20":"FDV", "30":"RTTY", "40":"DSTR"}
mode_Yaesu = {"01":"LSB", "02":"USB", "03":"CW-U", "04":"FM", "05":"AM", "06":"RTTY-L", 
              "07":"CW-L", "08":"DATA-L", "09":"RTTY-U", "0A":"DATA-FM", "0B":"FM-N",
              "0C":"DATA-U", "0D":"AM-N", "0E":"PKT", "0F":"DATA-FM-N"}

parser = argparse.ArgumentParser()
parser.add_argument('--vfostep', type=int, required=False, default=25, help='step of the vfo for JOG-A')
args = parser.parse_args()
vfoStep = args.vfostep
print(f"by default vfoStep is {vfoStep}")
# check if ini file exists and read the settings
inifile = 'midi2Cat.ini'
if os.path.isfile(inifile):
    ReadIniFile()
else:
    print("Configuration file does not exist, creating it")
    CreateIniFile()

#######################################
# define the serial port for radio
#######################################
try:
    radioSer = serial.Serial(
        # set the port parameters
        port=radioPort,
        baudrate=radioSpeed,
        bytesize=radioBits,
        stopbits=radioStop,
        parity=radioParity,
        xonxoff=radioXonXoff,  # software flow control
        rtscts=radioRtsCts,  # hardware (RTS/CTS) flow control
        dsrdtr=radioDsrDtr,  # hardware (DSR/DTR) flow control
        timeout=0.1)

    # open radio port
    # test if it is open
    ok = radioSer.is_open
    print('Is the Com open : %s ' % ok)
    # radioSer.close()

    # if COM port communication problem
except SerialException:
    print("No communication to", radioPort, ", check configuration file and available ports on computer !")
    sys.exit(1)
    
pygame.init()
"""window_resolution = (640, 180)
black = (0, 0, 0)
red = (255, 0, 0)
yellow = (255, 255, 25)
blue = (132, 180, 255)
f = 0.0
ACTION = 5
noAction = 0
# vfoStep = 100 now as argument --vfostep

pygame.display.set_caption("VFO A")
window_surface = pygame.display.set_mode(window_resolution)

digital_font = pygame.font.Font("digital-7 (mono).ttf", 130)
font_line2 = pygame.font.Font("digital-7 (mono).ttf", 24)
digital_font.set_underline(True)
"""
clock = pygame.time.Clock()
pygame.time.set_timer(pygame.USEREVENT, 100)

InitMidiDevice(midiDeviceIn)
my_input = pygame.midi.Input(midiDeviceIn)  # open Midi device
midi_out = pygame.midi.Output(midiDeviceOut)
blinkLED(2, 0.3, midi_out)
print("Nom du programme = " + __name__)
launched = True
loopi = 0
f = 0.0
ACTION = 5
noAction = 0
vfo = "A"
while launched:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            launched = False  # si on ferme avec la croix de l afenêtre
        elif event.type == pygame.USEREVENT:
            while f == 0.0:
                try:
                     if (kenwood or flex):
                            f = update_freq()
                            fa = f / 1000
                            strFreq = str("%6.3f" % fa)

                            pwrStr = read_power()
                            mode = GetMode()
                            mode_kenwood = ""
                            if debug >= 1: print("Mode is :", mode)
                     else:
                            f = update_freqIcom()
                            pwrStr = ""
                            mode = ""
                            #trx = str(PyCom.read_operating_mode())
                            #print(trx)
                            trx = ''
                except:
                     #f = 0.0
                     print('cant read the trx')
                     #f = update_freqIcom()
                     sys.exit()

    """
            window_surface.fill(black)
            if kenwood or flex:
                text = digital_font.render(strFreq, True, yellow)
            else:
                text = digital_font.render(f"{f:5.03f}", True, yellow)
            
            line2 = font_line2.render(f"vfo Step = {vfoStep} Hz, Power = " + pwrStr + " Watts" + " and Mode is " + mode, True, yellow)
            window_surface.blit(text, [10, 10])
            window_surface.blit(line2, [10, 150])
            pygame.display.flip()

        clock.tick(30)  # 60 images par seconde (60 fps)
    """
    if my_input.poll():
        midi_value = my_input.read(1)[0]
        if debug >= 1: print(midi_value)
        data = midi_value[0]
        midi_value[0] = []
        # print (data)
        # timestamp = event[1]
        device = data[0]
        status = data[1]
        control = data[2]
        value = data[3]
        # for debugging
        if debug >= 1: print(device, status, control, value)
        # print(status)
        # print(control)
        # print(value)

        if device == WT_DJ_JOGORPOT:  #  JOG or potentiometer
            if noAction < ACTION:  # 1 Action on 20 increment of the Jog
                noAction += 1
            if noAction >= ACTION:
                noAction = 0
            if status == WT_DJ_JOGA and noAction == 0:        # JOG A
                f = 0.0
                if kenwood or flex:
                    #vfo = "A"
                    if control == 127:
                        DownKenwood(vfoStep, vfo)
                    elif control == 1:
                        UpKenwood(vfoStep, vfo)
                else:
                    if control == 127 :  # Down
                        DownIcom(radioSer, vfoStep)
                    elif control == 1:
                        UpIcom(radioSer, vfoStep)
            elif status == WT_DJ_JOGB:      # JOG B
                if (control == 127) : # RIT down
                    if flex:
                        SendToRadio("ZZRD;")        # Rit Down
                    else:
                        SendToRadio("RD00025;")      # RIT down 25 Hz command
                elif (control == 1) :   # RIT Up
                    if flex:
                        SendToRadio("ZZRU;")        # Rit Up
                    else:
                        SendToRadio("RU00025;")            # RIT up 25 Hz command
            elif (status == WT_DJ_POTMEDIUMA) and flex:    # Pot. Medium A
                # DSP Filtering Bandwidth for VFO A
                SendToRadio("ZZFI0" + str(math.floor(7 * control / 127)) + ";")

            elif (status == WT_DJ_POTVOLUMEA) and kenwood: # Potard for AF Volume (0 --> 100 %)
                vol = math.floor(255 * control / 127)
                volStr = str("%03d" % vol)
                volString = "AG0" + volStr + ";"
                SendToRadio(volString)
                print(volString)
            elif (status == WT_DJ_POTVOLUMEB) and kenwood: # Potard for Monitor Volume (0 --> 100 %)
                vol = math.floor(9 * control / 127)
                volStr = str("%03d" % vol)
                volString = "ML" + volStr + ";"
                SendToRadio(volString)
                print(volString)
            elif (status == WT_DJ_POTBASSB) and kenwood: # Potard for vfoStep Volume (0 --> 100 %)
                vfoStep = math.floor(50 * control / 127)
                if vfoStep == 0: vfoStep = 1
                else: vfoStep = vfoStep * 10
                if vfoStep > 10 and vfoStep < 50 : vfoStep = 25
                elif vfoStep > 50 and vfoStep < 100 : vfoStep = 50
                elif vfoStep > 100 and vfoStep < 250 : vfoStep = 100
                elif vfoStep > 250 and vfoStep < 500 : vfoStep = 250
                print("vfoStep is ", vfoStep);
            elif (status == WT_DJ_CROSSFADER) and kenwood: # # Crossfader for power (0 --> 120 Watts)Potard for AF Volume (0 --> 100 Watts)
                pwr = math.floor(200 * control / 127)
                pwrStr = str("%03d" % pwr)
                # print( pwrStr)
                pwrString = "PC" + pwrStr + ";"
                SendToRadio(pwrString)

        elif device == WT_DJ_PUSH_BUTTON and kenwood:  # Buttons
            if status == WT_DJ_BTN_REC and control > 64:  # Rec button               
                if vfoStep >= 1000:
                    vfoStep = 100
                elif vfoStep == 100:
                    vfoStep = 25
                elif vfoStep == 25:
                    vfoStep = 10
                elif vfoStep == 10:
                    vfoStep = 1
                else: vfoStep = 1000
                print("You push the REC button and now vfoStep is", vfoStep)
            elif status == WT_DJ_BTN_3A:       # Button 3A for PTT
                if control == 127:
                    SendToRadio("TX0;")
                elif control == 0:
                    SendToRadio("RX;")
            elif status == WT_DJ_BTN_3B and control == 127:  # Button 3B for Noise Blanker
                if read_nb() == "0" :
                    nbToSent = "NB1;"
                    print("Sent command Noise Blanker On" )
                else:
                    nbToSent = "NB0;"
                    print("Sent command Noise Blanker Off")
                SendToRadio(nbToSent)
            elif status == WT_DJ_BTN_4B and control == 127:  # Button 4B for Noise Reduction
                if read_nr() == "0" :
                    nrToSent = "NR1;"
                    print("Sent command Noise Reduction On" )
                else:
                    nrToSent = "NR0;"
                    print("Sent command Noise Reduction Off")
                SendToRadio(nrToSent)
            elif status == WT_DJ_BTN_PLAY_A and control == 127:  # Button PLAY_A
                    #SendToRadio("RT1;")  # RIT on
                vfo = "B"
                print("You push the Play_A button")
            elif status == WT_DJ_BTN_SYNC_A and control == 127:  # Button Sync_A
                #SendToRadio("RT1;")  # RIT on
                vfo = "A"
                print("You push the Sync_A button")        
            elif status == WT_DJ_BTN_SYNC_B  and control == 127:       # Button SYNC_B
                SendToRadio("RT0;")  # RIT Off
            elif status == WT_DJ_BTN_CUE_B  and control == 127:       # Button CUE_B
                SendToRadio("RC;")   # RIT Clear
            elif status == WT_DJ_BTN_PLAY_B and control == 127:  # Button PLAY_B
                SendToRadio("RT1;")  # RIT on
            elif status == WT_DJ_BTN_MODE and control == 127:      # Button Mode
                mode = GetMode()
                if mode == "3":
                    newMode = "1"
                elif mode == "1":
                    newMode = "2"
                elif mode == "2":
                    newMode = "4"
                elif mode == "4":
                    newMode = "6"
                elif mode == "6":
                    newMode = "9"
                elif mode == "9":
                    newMode = "5"
                elif mode == "5":
                    newMode = "3"
                strCat = "MD" + newMode + ";"
                SendToRadio(strCat)
                strMode = str(MODE(int(newMode)))
                print("New mode is " + strMode)
            elif status == WT_DJ_BTN_1B and control == 127:       # Button 1B for teAttst
                SendToRadio("AT00;")
                print("You push the 1B button")
            elif status == WT_DJ_BTN_4A and control == 127:       # Button 4A for test
                SendToRadio("GT001;")
                print("You push the 4A button")