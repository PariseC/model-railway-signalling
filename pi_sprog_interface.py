#----------------------------------------------------------------------
# This module provides a basic CBUS interface for sending and receiving
# commands for the control of points and signals on the layout.
# It has been specifically designed to drive the Pi-SPROG-3 via the
# UART serial interface on the Raspberry PI.
#
# It is not meant to provide a fully-functional interface for All DCC command
# and control functions - just the minimum set needed to support the driving
# of signals and points via a selection of common DCC Accessory decoders:
#
# The following functions are designed to be called by external modules:
#
# initialise_pi_sprog (Sends RTON event and waits for track power ON acknowledgement):
#   Optional Parameters:
#       debug:int 0 = No debug, 1 = status messages only, 2 = all CBUS messages - Default = 0
#
# send_accessory_short_event
#   Mandatory Parameters:
#       address:int - The Device number of the accessory to be switched (the DCC Address)
#       status:bool - State to switch it to (True=ON, False = OFF)
#
#
# Functions are also included in the Code base for sending direct DCC accessory Packets
# and Extended DCC Accessory Packets. However, I have been unable to confirm either by
# Research or Test whether these are supported by the Pi-SPROG-3
#
# Decoder Programming is not supported - Recommendation is to use the JRMI DecoderPro
# software to configure the accessory decoders as appropriate to their use
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Note that the Pi-SPROG-3 needs the UART interfaces to be swapped so that
# serial0 is routed to the GPIO connector instead of being used for BlueTooth.
# The configuration procedure is documented below
#
# 1) Download the uart-rtscts overlay:
#    wget https://raw.github.com/HiassofT/AtariSIO/master/contrib/rpi/uart- ctsrts.dtbo
# 2) Copy it to the required directory:
#    sudo cp uart-ctsrts.dtbo /boot/overlays/
# 3) Add the overlays to the end of config.txt:
#    sudo nano /boot/config.txt - and then add the following lines:
#       dtoverlay=miniuart-bt
#       enable_uart=1
#       dtoverlay=uart-ctsrts
# 4) Edit the command line to prevent the Kernel using the UART at startup:
#    sudo nano /boot/cmdline.txt 
#        Remove ‘console=serial0,115200’
#        Note that this file must contain only one line
# 5) Reboot the Raspberry Pi
# ---------------------------------------------------------------------

import threading
import serial
import time

# Create a new class of the Serial Port (port is configured/opened later)

serial_port = serial.Serial ()

# Global Variables (constants used by the fuctions in the module)

can_bus_id = 1                # The arbitary CANBUS ID we will use for the Pi
pi_cbus_node = 1              # The arbitary CBUS Node ID we will use for the Pi
transmit_delay = 0.02         # The delay between sending CBUS Messages (in seconds)

# Global Variables (configured/changed by the functions in themodule)

track_power_on = False        # if the track power is OFF we wont try sending any commands
debug_level = 0               # 0 = No debug messages, 1 = basic messages, 2 = all sent/received messages
sprog_cbus_node = 0           # The CBUS Node ID for the Sprog (This is read from the SPROG)

# This is the output buffer for messages to be sent to the SPROG
# We use a buffer so we can throttle the transmit rate without blocking
output_buffer = []            

#------------------------------------------------------------------------------
# Internal thread to write queued CBUS messages to the Serial Port with a
# short delay inbetween each message. We do this because some decoders don't
# seem to process messages sent to them in quick succession - and if the
# decoder "misses" an event the signal/point may end up in an erronous state
#------------------------------------------------------------------------------

def thread_to_send_buffered_data ():

    global output_buffer
    global debug_level
    global transmit_delay
    
    while True:
        
        # Perform a short sleep so the thread doesn't max out the CPU
        time.sleep (0.001)
        
        # Check if there are any messages in the output buffer that need to be sent
        if len(output_buffer) > 0:
            
            # Read the first CBUS Message from the list and then remove from the list
            command_string = output_buffer[0]
            output_buffer.pop(0)
            
            # Print the Transmitted message (if the appropriate debug level is set)
            if debug_level > 1: print ("PI >> SPROG - CBUS - " + command_string)
            
            # Write the CBUS Message to the serial port
            serial_port.write(bytes(command_string,"Ascii"))
            
            # Sleep before sending the next CBUS message
            time.sleep(transmit_delay)
    

#------------------------------------------------------------------------------
# Internal thread to read CBUS messages from the Serial Port and make a callback
# We're not receiving anything else on this port so its OK to set up the port 
# without a timeout - as we are only interested in "complete" messages
#------------------------------------------------------------------------------

def thread_to_read_received_data ():

    global debug_level
    global sprog_cbus_node
    global pi_cbus_node
    global track_power_on
    
    while True:
        
        # Perform a short sleep so the thread doesn't max out the CPU
        time.sleep (0.001)
        
        # Read from the port until we get the GridConnect Protocol message termination character
        byte_string = serial_port.read_until(b";")
        
        # Print the Received message (if the appropriate debug level is set)
        if debug_level > 1: print("SPROG >> Pi - CBUS - " + byte_string.decode('Ascii') + "\r")
        
        # Extract the OpCode - so we can decide what to do
        op_code = int((chr(byte_string[7]) + chr(byte_string[8])),16)
        
        # Process selected commands (note that only a subset is supported)
        
        if op_code == 227:  # Command Station Status Report
            
            # Get the node number - Encoded across 4 hex characters
            sprog_cbus_node = int(chr(byte_string[9]) + chr(byte_string[10]) +
                    chr(byte_string[11]) + chr(byte_string[12]),16)
            
            # Print out the status report (if the appropriate debug level is set)
            if debug_level > 0:
                print ("SPROG >> PI - STAT (Command Station Status Report)")
                print ("    Node Id       :", sprog_cbus_node)
                print ("    CS Number     :", int(chr(byte_string[13]) + chr(byte_string[14]),16))
                print ("    Version       :", int(chr(byte_string[17]) + chr(byte_string[18]),16), ".",
                        int(chr(byte_string[19]) + chr(byte_string[20]),16),".",
                        int(chr(byte_string[21]) + chr(byte_string[22]),16))

                # Get the Flags - we only need the last hex character (to get the 4 bits)
                flags = int(chr(byte_string[16]),16)
                print ("    Reserved      :", ((flags & 0x080)==0x80))
                print ("    Service Mode  :", ((flags & 0x040)==0x40))
                print ("    Reset Done    :", ((flags & 0x02)==0x20))
                print ("    Emg Stop Perf :", ((flags & 0x10)==0x10))
                print ("    Bus On        :", ((flags & 0x08)==0x08))
                print ("    Track On      :", ((flags & 0x04)==0x04))
                print ("    Track Error   :", ((flags & 0x02)==0x02))
                print ("    H/W Error     :", ((flags & 0x01)==0x01), "\r")

        elif op_code == 182:  # Response to Query Node
            
            # Get the node number - Encoded across 4 hex characters
            sprog_cbus_node = int(chr(byte_string[9]) + chr(byte_string[10]) +
                    chr(byte_string[11]) + chr(byte_string[12]),16)
            
            # Print out the status report (if the appropriate debug level is set)
            if debug_level > 0:
                print ("SPROG >> PI - PNN  (Response to Query Node)")
                print ("    Node Id   :", sprog_cbus_node)
                print ("    Mfctre ID :", int(chr(byte_string[13]) + chr(byte_string[14]),16))
                print ("    Module ID :", int(chr(byte_string[15]) + chr(byte_string[16]),16))
                
                # Get the Flags - we only need the last hex character (to get the 4 bits)
                flags = int(chr(byte_string[18]),16)
                print ("    Bldr Comp :", ((flags & 0x08)==0x08))
                print ("    FLiM Mode :", ((flags & 0x04)==0x04))
                print ("    Prod Node :", ((flags & 0x02)==0x02))
                print ("    Cons Node :", ((flags & 0x01)==0x01), "\r")

        elif op_code == 82:  # Node Number Acknowledge
            
            # Get the node number - Encoded across 4 hex characters
            sprog_cbus_node = int(chr(byte_string[9]) + chr(byte_string[10]) +
                    chr(byte_string[11]) + chr(byte_string[12]),16)
            
            if debug_level > 0:
                print ("SPROG >> PI - NNACK (Node Number Acknowledge) - Node Id:",sprog_cbus_node, "\r")

        elif op_code == 4:  # Track Power is OFF
            
            if debug_level > 0: print ("SPROG >> PI - TOF  (Track OFF)")
            
        elif op_code == 5:  # Track Power is ON
            
            if debug_level > 0: print ("SPROG >> PI - TON  (Track ON)")
            track_power_on = True
    
    return()

#------------------------------------------------------------------------------
# Internal function to encode a CBUS Command in the GridConnect protocol and send to
# the specified comms port. The format of a CBUS Command is summarised as follows:
#
# CBUS Commands are sent as an ASCII strings starting with ':' and followed by 'S'
# The next 4 characters are the Hex representation of the 11 bit CAN Header
#         Major Priority - Bits 9 & 10 (00 = Emergency; 01 = High Priority, 10 = Normal)
#         Minor Priority - Bits 7 & 8 (00 = High, 01 = Above Normal, 10 = Normal, 11 = Low)
#         CAN BUS ID - Bits 0-6 (CAN segment unique ID)
#     Note that The 11 CAN Header Bits are encoded into the 2 Bytes LEFT JUSTIFIED
#     So the Header bytes end up as: P P P P A A A A | A A A 0 0 0 0 0
# The next character is 'N' - specifying a 'Normal' CBUS Frame (all we need to use)
# The next 2 characters are the Hex representation of the 1 byte OPCODE 
# The remaining characters represent the data bytes (0 to 7 associated with the OPCODE)
# Finally the string is terminated with a ';' (Note there is no '\r' required)
#
# References for Header Encoding - CBUS Developers Guide - Section 6.1, 6.4, 12.2
#
# Example - can_id=99 , mj_pri=2, min_pri=2, op_code=9 (RTON - request track on)
# encodes into a CBUS Command 'SAC60N09;'
#------------------------------------------------------------------------------

def send_cbus_command (mj_pri:int, min_pri:int, op_code:int, *data_bytes:int):

    global debug_level
    global can_bus_id

    if (mj_pri < 0 or mj_pri > 2):
        print("Error: send_cbus_command - Invalid Major Priority "+str(mj_pri))
    elif (min_pri < 0 or min_pri > 3):
        print("Error: send_cbus_command - Invalid Minor Priority "+str(min_pri))
    elif (op_code < 0 or op_code > 255):
        print("Error: send_cbus_command - Op Code out of range "+str(op_code))
        
    else:    
        # Encode the CAN Header        
        header_byte1 = (mj_pri << 6) | (min_pri <<4) | (can_bus_id >> 3)
        header_byte2 = (0x1F & can_bus_id) << 5
        
        # Start building the GridConnect Protocol string for the CBUS command
        command_string = (":S" + format(header_byte1,"02X") + format(header_byte2,"02X")
                          + "N" + format (op_code,"02X"))
        
        # Add the Data Bytes associated with the OpCode (if there are any)
        for data_byte in data_bytes: command_string = command_string + format(data_byte,"02X")
        
        # Finally - add the command string termination character
        command_string = command_string + ";"
        
        # Add the command to the output buffer (to be picked up by the Tx thread)
        output_buffer.append(command_string)
        
    return()

#------------------------------------------------------------------------------
# Externally Called Function to establish basic comms with the PI-SPROG
# All this does (with debug_level = 0) is to send a command to request
# Track Power is on and waits for the confirmation response. With Debug
# Level set >0 it also requests the status of the Command station
#------------------------------------------------------------------------------

def initialise_pi_sprog (debug:int = 0):

    global debug_level
    global track_power_on

    # Assign the global debug level (used across all other functions)
    debug_level = debug
    
    if debug_level > 0: print ("initialise_pi_sprog - Opening Serial Port")

    # We're not receiving anything else on this port so its OK to set up the port without
    # a timeout - as we are only interested in "complete" messages (terminated by ';')

    serial_port.baudrate = 115200
    serial_port.port = "/dev/serial0"
    serial_port.bytesize = 8
    serial_port.timeout = None
    serial_port.parity = serial.PARITY_NONE
    serial_port.stopbits = serial.STOPBITS_ONE
    serial_port.open()
    
    # Start the thread to read buffered responses from the PI-SPROG
    thread = threading.Thread (target=thread_to_read_received_data)
    thread.start()

    # Start the thread to send buffered commands to the PI-SPROG
    thread = threading.Thread (target=thread_to_send_buffered_data)
    thread.start()

    # If Debug Level 2 is selected - we'll request the status of the Pi-Sprog
    if debug_level > 1:
        print ("PI >> SPROG - RSTAT (Request Command Station Status)")
        send_cbus_command (mj_pri=2, min_pri=2, op_code=12)
        time.sleep (1.0)

#    if debug_level > 0: print ("PI >> SPROG - QNN (Query Node Number)")
#    send_cbus_command (mj_pri=2, min_pri=3, op_code=13)
    
    # Send the command to switch on the Track Supply (to the DCC Bus)
    if debug_level > 0: print ("PI >> SPROG - RTON (Request Track On)")
    send_cbus_command (mj_pri=2, min_pri=2, op_code=9)

    # Now wait until we get confirmation thet the Track power is on
    # If the SPROG hasn't responded in 5 seconds its not going to respond at all
    timeout_start = time.time()
    while time.time() < timeout_start + 5:
        if track_power_on:break
    
    if not track_power_on: print("Error: initialise_pi_sprog - No response to RTON Request")

    return ()

#------------------------------------------------------------------------------
# Externally Called Function to send an Accessory Short CBUS On/Off Event
#------------------------------------------------------------------------------

def send_accessory_short_event (address:int, active:bool):
    
    global pi_cbus_node
    global track_power_on

    if (address < 1 or address > 2047):
        print("Error: send_accessory_short_event - Invalid address "+str(address))

    # Only try to send the command if the PI-SPROG-3 has initialised correctly

    elif track_power_on:
        
        byte1 = (pi_cbus_node & 0xff00) >> 8
        byte2 = (pi_cbus_node & 0x00ff)
        byte3 = (address & 0xff00) >> 8
        byte4 = (address & 0x00ff)
          
        #  Send a ASON or ASOF Command (Accessoy Short On or Accessory Short Off)
        if active:
            if debug_level > 0: print ("PI >> SPROG - ASON (Accessory Short ON)  : " + str(address))
            send_cbus_command (2, 3, 152, byte1, byte2, byte3, byte4)

        else:
            if debug_level > 0: print ("PI >> SPROG - ASOF (Accessory Short OFF) : " + str(address))
            send_cbus_command (2, 3, 153, byte1, byte2, byte3, byte4)

    return ()

#------------------------------------------------------------------------------
# Function to encode a standard 3-byte DCC Accessory Decoder Packet into 3 bytes
# for transmission to the PI-SPROG as a RDCC3 Command (Request 3-byte DCC Packet).
# Calls the 'send_cbus_command' function to actually encode and send the command
# The DCC Packet is sent <repeat> times - but not refreshed on a regular basis
# Acknowledgement to Java NMRA implementation (which this function follows closely)
# 
# Packets are represented by an array of bytes. Preamble/postamble not included.
# Note that this is a data representation, NOT a representation of the waveform!
# From the NMRA RP: 0 10AAAAAA 0 1AAACDDD 0 EEEEEEEE 1, Where
#    A = Address bits
#    D = the output channel to set
#    C = the State (1 = ON, 0 = OFF) 
#    E = the error detection bits
#
# Accessory Digital Decoders can control momentary or constant-on devices, the duration
# of time that each output is active being pre-configured by CVs #515 through #518.
# Bit 3 of the second byte "C" is used to activate or deactivate the addressed device.
# (Note if the duration the device is intended to be on is less than or equal the
# pre-configured duration, no deactivation is necessary)
#
# Since most devices are paired, the convention is that bit "0" of the second byte
# is used to distinguish between which of a pair of outputs the accessory decoder is
# activating or deactivating.
#
# Bits 1 and 2 of the second byte is used to indicate which of 4 pairs of outputs the
# accessory decoder is activating or deactivating
#
# The significant bits of the 9 bit address are bits 4-6 of the second data byte.
# By convention these three bits are in ones complement. The use of bit 7 of the second
# byte is reserved for future use.
#
# NOTE - This function is currently untested as I have been unable to confirm
# (either via research or Test) whether the Pi-SPROG-3 supports the RDDC3 Command 
#------------------------------------------------------------------------------

def send_DCC_accessory_decoder_packet (address:int, active:bool, output_channel:int = 0, repeat:int = 3):

    global track_power_on
    global debug_level
    
    if (address < 1 or address > 511):
        print("Error: send_accessory_decoder_packet - Invalid address "+str(address))
    
    elif (output_channel < 0 or output_channel > 7):
        print("Error: send_accessory_decoder_packet - Invalid output channel " +
                      str(output_channel)+" for address "+str(address))    

    elif (repeat < 0 or repeat > 255):
        print("Error: send_accessory_decoder_packet - Invalid Repeat Value " +
                      str(repeat)+" for address "+str(address))

    # Only try to send the command if the PI-SPROG-3 has initialised correctly

    elif track_power_on:
        
        low_addr = address & 0x3F
        high_addr = (( ~ address) >> 6) & 0x07
        
        byte1 = (0x80 | low_addr);
        byte2 = (0x80 | (high_addr << 4) | (active << 3) | output_channel & 0x07);
        byte3 = (byte1 ^ byte2)
        
        #  Send a RDCC3 Command (Request 3-Byte DCC Packet) via the CBUS
        if debug_level > 0: print ("PI >> SPROG - RDCC3 (Send 3 Byte DCC Packet) : Address:"
                        + str(address) + "  Channel:" + str(output_channel) +"  State:" + str(active))
        send_cbus_command (2, 2, 128, repeat, byte1, byte2, byte3)

    return ()

#------------------------------------------------------------------------------
# Function to encode a standard Extended DCC Accessory Decoder Packet into 4 bytes
# for transmission to the PI-SPROG as a RDCC4 Command (Request 4-byte DCC Packet).
# Calls the 'send_cbus_command' function to actually encode and send the command
# The DCC Packet is sent <repeat> times - but not refreshed on a regular basis
# Acknowledgement to Java NMRA implementation (which this function follows closely)
#
# Packets are represented by an array of bytes. Preamble/postamble not included.
# From the NMRA RP:  10AAAAAA 0 0AAA0AA1 0 000XXXXX 0 EEEEEEEE 1}
#    A = Address bits
#    X = The Aspect to display
#    E = the error detection bits
#
# The addressing is not clear in te NRMA standard - Two interpretations are provided
# in the code (albeit one commented out) - thanks again to the Java NMRA implementation
#
# NOTE - This function is currently untested as I have been unable to confirm
# (either via research or Test) whether the Pi-SPROG-3 supports the RDDC4 Command 
#------------------------------------------------------------------------------

def send_extended_DCC_accessory_decoder_packet (address:int, aspect:int, repeat:int = 3):

    global track_power_on
    global debug_level

    if (address < 1 or address > 2044):
        print("Error: send_extended_DCC_accessory_decoder_packet - Invalid address "+str(address))
        
    elif (aspect < 0 or aspect > 31):
        print("Error: send_extended_DCC_accessory_decoder_packet - Invalid aspect "+str(aspect))
        
    elif track_power_on:
        
#        #Interpretation 1
#        address -= 1; 
#        low_addr = (address & 0x03); 
#        board_addr = (address >> 2) + 1; 

        # Interpretation 2
        address -= 1; 
        low_addr = (address & 0x03);  
        board_addr = (address >> 2); 

        mid_addr = board_addr & 0x3F;
        high_addr = ((~board_addr) >> 6) & 0x07;

        byte1 = (0x80 | mid_addr);
        byte2 = (0x01 | (high_addr << 4) | (low_addr << 1));
        byte3 = (0x1F & aspect);
        byte4 = (byte1 ^ byte2 ^ byte3);
        
        #  Send a RDCC4 Command (Request 4-Byte DCC Packet) via the CBUS
        if debug_level > 0: print ("PI >> SPROG - RDCC4 (Send 4 Byte DCC Packet) : Address:"
                        + str(address) + "  Aspect:" + str(aspect))
        send_cbus_command (2, 2, 160, repeat, byte1, byte2, byte3, byte4)

    return()

###########################################################################
