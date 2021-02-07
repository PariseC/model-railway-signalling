# --------------------------------------------------------------------------------
# This module is used for creating and managing signal objects
#
# Currently supported types:
#    1) Colour Light Signals - 3 or 4 aspect or 2 aspect (home, distant or red/ylw)
#           - with or without a position light subsidary signal
#           - with or without route indication feathers (maximum of 4)
#           - with or without a theatre type route indicator
#    2) Ground Position Light Signals
#           - groud position light or shunt ahead position light
#           - either early or modern (post 1996) types
#
# The following functions are designed to be called by external modules
#
# create_colour_light_signal - Creates a colour light signal
#   Mandatory Parameters:
#       Canvas - The Tkinter Drawing canvas on which the point is to be displayed
#       sig_id:int - The ID for the signal - also displayed on the signal button
#       x:int, y:int - Position of the point on the canvas (in pixels) 
#   Optional Parameters:
#       signal_subtype:sig_sub_type - Subtype of colour light signal to create - Default -four_aspect
#                                     'three_aspect' and 'four_aspect' signal types are supported
#                                     Also 2 aspect signal types of 'home', 'distant', 'red_ylw'
#       orientation:int- Orientation in degrees (0 or 180) - Default is zero
#       sig_callback:name - Function to call when a signal event happens - Default is null
#       sig_passed_button:bool - Creates a "signal Passed" button for automatic control - Default False
#       position_light:bool - Creates a subsidary position light signal - Default False
#       lhfeather45:bool - Creates a LH route indication feather at 45 degrees - Default False
#       lhfeather90:bool - Creates a LH route indication feather at 90 degrees - Default False
#       rhfeather45:bool - Creates a RH route indication feather at 45 degrees - Default False
#       rhfeather90:bool - Creates a RH route indication feather at 90 degrees - Default False
#       theatre_route_indicator:bool -  Creates a Theatre Type route indicator - Default False
#       fully_automatic:bool - Creates a signal without any manual controls - Default False
#
# create_ground_position_signal - created a grund position light signal
#   Mandatory Parameters:
#       Canvas - The Tkinter Drawing canvas on which the point is to be displayed
#       sig_id:int - The ID for the signal - also displayed on the signal button
#       x:int, y:int - Position of the point on the canvas (in pixels) 
#   Optional Parameters:
#       orientation:int- Orientation in degrees (0 or 180) - Default is zero
#       sig_callback:name - Function to call when a signal event happens - Default is null
#       sig_passed_button:bool - Creates a "signal Passed" button for automatic control - Default False
#       shunt_ahead:bool - Specifies a shunt ahead signal (yellow/white aspect) - default False
#       modern_type: bool - Specifies a modern type ground position signal (post 1996) - Default False
#
# set_route_indication - Set (and change) the route indication for the signal
#   Mandatory Parameters:
#       sig_id:int - The ID for the signal
#   Optional Parameters:
#       feathers:route_type - MAIN (no feathers displayed), LH1, LH2, RH1 or RH2 - default 'MAIN'
#       theatre_text:str  - The text to display in the theatre route indicator - default empty string
#          - Note that both Feathers and theatre text can be specified in the call
#          - What actually gets displayed will depend on what the signal was created with
#
# update_signal - update the aspect based on the aspect of the signal ahead
#               - mainly intended for 3 and 4 aspect colour light signals but
#               - can also be used to set the aspect of 2 aspect distant signals
#   Mandatory Parameters:
#       sig_id:int - The ID for the signal
#   Optional Parameters:
#       sig_ahead_id:int - The ID for the signal "ahead" of the one we want to set
#
# lock_signal(*sig_id) - to enable external point/signal interlocking functions
#                       - One or more Signal IDs can be specified in the call
#
# unlock_signal(*sig_id) - to enable external point/signal interlocking functions
#                       - One or more Signal IDs can be specified in the call
#
# lock_subsidary_signal(*sig_id) - to enable external point/signal interlocking functions
#                       - One or more Signal IDs can be specified in the call
#
# unlock_subsidary_signal(*sig_id) - to enable external point/signal interlocking functions
#                       - One or more Signal IDs can be specified in the call
#
# signal_clear(sig_id) - returns the state of the signal (True/False - True if 'clear')
#
# subsidary_signal_clear(sig_id) - returns the state of the subsidary signal (True/False- True if 'clear')
#
# set_signal_override (sig_id*) - Overrides the signal and sets it to "ON"
#                       - One or more Signal IDs can be specified in the call
#
# clear_signal_override (sig_id*) - Clears the override and reverts the signal to the controlled state
#                       - One or more Signal IDs can be specified in the call
#
# trigger_timed_signal - Sets the signal to "ON"  and then automatically cycles through the aspects back to green
#                       - If a start delay >0 is specified then a 'sig_passed' callback event will be generated
#                       - when the signal is first changed to RED - For each subsequent aspect change (all the
#                       - way back to GREEN) 'sig_updated' callback event will be generated
#   Mandatory Parameters:
#       sig_id:int - The ID for the signal
#   Optional Parameters:
#       start_delay:int - Delay (in seconds) before changing to Red (default=5)
#       time_delay:int - Delay (in seconds) for cycling through the spects (default=5)
# 
# -------------------------------------------------------------------------
   
# Specify the external Modules we need to import

from tkinter import *
import signals_common
import signals_colour_lights

# -------------------------------------------------------------------------
# Externally called Functions and classes to create the specific signal types
# These are imported into the current context so they "exist" within the
# context of the main "Signals" Module so external programmes only need
# to import the 'signals' modules to make use of these classes/functions
# e.g. An external module would use 'Signals.create_colour_light_signal (...)'
# -------------------------------------------------------------------------

from signals_common import sig_type
from signals_common import route_type
from signals_common import sig_callback_type

from signals_colour_lights import create_colour_light_signal
from signals_ground_position import create_ground_position_signal
from signals_colour_lights import signal_sub_type

# -------------------------------------------------------------------------
# Externally called Function to update a signal according the state of the
# Signal ahead - Intended mainly for Coulour Light Signal types so we can
# ensure the "CLEAR" aspect reflects the aspect of ths signal ahead
# Calls the signal type-specific functions depending on the signal type
# -------------------------------------------------------------------------

def update_signal (sig_id:int, sig_ahead_id:int = 0):

    # Validate the signal exists and it is not a Ground Position Signal
    if not signals_common.sig_exists(sig_id):
        print ("ERROR: update_signal - Signal "+str(sig_id)+" does not exist")
    
    elif sig_ahead_id != 0 and not signals_common.sig_exists(sig_ahead_id): 
        print ("ERROR: update_signal - Signal Ahead "+str(sig_ahead_id)+" does not exist")
        
    elif sig_id == sig_ahead_id: 
        print ("ERROR: update_signal - Signal Ahead "+str(sig_ahead_id)+" is the same ID")
        
    else:
        # get the signals that we are interested in
        signal = signals_common.signals[str(sig_id)]
        
        # now call the signal type-specific functions to update the signal
        if signal["sigtype"] == sig_type.colour_light:
            signals_colour_lights.update_colour_light_signal_aspect (sig_id,sig_ahead_id )
        
    return()

# -------------------------------------------------------------------------
# Externally called function to set the route indication for the signal
# Calls the signal type-specific functions depending on the signal type
# -------------------------------------------------------------------------

def set_route_indication (sig_id:int, route:route_type = route_type.MAIN, theatre_text:str =""):

    # Validate the signal exists and it is not a Ground Position Signal
    if not signals_common.sig_exists(sig_id):
        print ("ERROR: set_route_indication - Signal "+str(sig_id)+" does not exist")
        
    else:
        # get the signals that we are interested in
        signal = signals_common.signals[str(sig_id)]
        
        # now call the signal type-specific functions to update the signal
        if signal["sigtype"] == sig_type.colour_light:
            signals_colour_lights.update_colour_light_route_indication (sig_id,route,theatre_text)
                        
    return()

# -------------------------------------------------------------------------
# Externally called function to Return the current state of the signal
# -------------------------------------------------------------------------

def signal_clear (sig_id:int):
        
    # Validate the signal exists and it is not a Ground Position Signal
    if not signals_common.sig_exists(sig_id):
        print ("ERROR: signal_clear - Signal "+str(sig_id)+" does not exist")
        sig_clear = False
        
    else:
        # get the signal that we are interested in
        signal = signals_common.signals[str(sig_id)]
        sig_clear = signal["sigclear"]
        
    return (sig_clear)

# -------------------------------------------------------------------------
# Externally called function to Return the current state of the subsidary
# signal - if the signal does not have one then the return will be FALSE
# -------------------------------------------------------------------------

def subsidary_signal_clear (sig_id:int):
        
    # Validate the signal exists
    if not signals_common.sig_exists(sig_id):
        print ("ERROR: subsidary_signal_clear - Signal "+str(sig_id)+" does not exist")
        sig_clear = False
        
    else:
        # get the signals that we are interested in
        signal = signals_common.signals[str(sig_id)]
        sig_clear = signal["subclear"]
            
    return (sig_clear)

# -------------------------------------------------------------------------
# Externally called function to Lock the signal (preventing it being cleared)
# Multiple signal IDs can be specified in the call
# -------------------------------------------------------------------------

def lock_signal (*sig_ids:int):
        
    for sig_id in sig_ids:
        # Validate the signal exists
        if not signals_common.sig_exists(sig_id):
            print ("ERROR: lock_signal - Signal "+str(sig_id)+" does not exist")  
        else:   
            # get the signal that we are interested in
            signal = signals_common.signals[str(sig_id)]
            
            # If signal/point locking has been correctly implemented it should
            # only be possible to lock a signal that is "ON" (i.e. at DANGER)
            if signal["sigclear"]: print ("WARNING: lock_signal - Signal "+ str(sig_id) +" is CLEAR")
            
            # Disable the Signal button to lock it
            signal["sigbutton"].config(state="disabled")
            
    return()

# -------------------------------------------------------------------------
# Externally called function to Unlock the main signal
# Multiple signal IDs can be specified in the call
# -------------------------------------------------------------------------

def unlock_signal (*sig_ids:int):
        
    for sig_id in sig_ids:
        # Validate the signal exists
        if not signals_common.sig_exists(sig_id):
            print ("ERROR: unlock_signal - Signal "+str(sig_id)+" does not exist")
            
        else:   
            # get the signal that we are interested in
            signal = signals_common.signals[str(sig_id)]
            
            # Enable the Signal button to unlock it (if its not a fully automatic signal)
            if not signal["automatic"]:
                signal["sigbutton"].config(state="normal")
            
    return()

# -------------------------------------------------------------------------
# Externally called function to Lock the subsidary signal
# This is effectively a seperate signal from the main aspect
# Multiple signal IDs can be specified in the call
# -------------------------------------------------------------------------

def lock_subsidary_signal (*sig_ids:int):
        
    for sig_id in sig_ids:
        # Validate the signal exists
        if not signals_common.sig_exists(sig_id):
            print ("ERROR: lock_subsidary - Signal "+str(sig_id)+" does not exist")
            
        else:
            # get the signal that we are interested in
            signal = signals_common.signals[str(sig_id)]
            
            # If signal/point locking has been correctly implemented it should
            # only be possible to lock a signal that is "ON" (i.e. at DANGER)
            if signal["subclear"]: print ("WARNING: lock_subsidary_signal - Subsidary signal "+ str(sig_id) +" is CLEAR")
            
            # Disable the Button to lock the subsidary signal
            signal["subbutton"].config(state="disabled")        
                
    return()

# -------------------------------------------------------------------------
# Externally called function to Unlock the subsidary signal
# This is effectively a seperate signal from the main aspect
# Multiple signal IDs can be specified in the call
# -------------------------------------------------------------------------

def unlock_subsidary_signal (*sig_ids:int):
        
    for sig_id in sig_ids:
        # Validate the signal exists
        if not signals_common.sig_exists(sig_id):
            print ("ERROR: unlock_subsidary - Signal "+str(sig_id)+" does not exist")
            
        else:
            # get the signal that we are interested in
            signal = signals_common.signals[str(sig_id)]
            
            # Re-enable the Button to unlock the subsidary signal
            signal["subbutton"].config(state="normal") 
                
    return()

# -------------------------------------------------------------------------
# Externally called function to Override a signal - effectively setting it
# to RED (apart from 2 aspect distance signals - which are set to YELLOW)
# Signal will display the overriden aspect no matter what its current setting is
# Used to support automation - e.g. set asignal to Danger once a train has passed
# Multiple signal IDs can be specified in the call
# -------------------------------------------------------------------------

def set_signal_override (*sig_ids:int):
    
    for sig_id in sig_ids:
        # Validate the signal exists
        if not signals_common.sig_exists(sig_id):
            print ("ERROR: set_signal_override - Signal "+str(sig_id)+" does not exist")
            
        else:
            # get the signal that we are interested in
            signal = signals_common.signals[str(sig_id)]
            
            # Set the override state and change the button text to indicate override
            signal["override"] = True
            signal["sigbutton"].config(fg="red", disabledforeground="red")

            # Update the dictionary of signals
            signals_common.signals[str(sig_id)] = signal
            
            # now call the signal type-specific functions to update the signal
            if signal["sigtype"] == sig_type.colour_light:
                signals_colour_lights.update_colour_light_signal_aspect (sig_id)
                
    return()

# -------------------------------------------------------------------------
# Externally called function to Clear a Signal Override 
# Signal will revert to its current manual setting (on/off) and aspect
# Multiple signal IDs can be specified in the call
# -------------------------------------------------------------------------

def clear_signal_override (*sig_ids:int):
            
    for sig_id in sig_ids:
        # Validate the signal exists
        if not signals_common.sig_exists(sig_id):
            print ("ERROR: clear_signal_override - Signal "+str(sig_id)+" does not exist")
            
        else:
            # get the signal that we are interested in
            signal = signals_common.signals[str(sig_id)]
            
            # Clear the override and change the button colour
            signal["override"] = False
            signal["sigbutton"].config(fg="black",disabledforeground="grey50")
                
            # Update the dictionary of signals
            signals_common.signals[str(sig_id)] = signal

            # Check the signal type supports this feature
            if signal["sigtype"] == sig_type.colour_light:
                
            # now call the signal type-specific functions to update the signal
                signals_colour_lights.update_colour_light_signal_aspect (sig_id)

    return()

# -------------------------------------------------------------------------
# Externally called Function to 'override' a signal (changing it to 'ON') after
# a specified time delay and then clearing the override the signal after another
# specified time delay. In the case of colour light signals, this will cause the
# signal to cycle through the supported aspects all the way back to GREEN. When
# the Override is cleared, the signal will revert to its previously displayed aspect
# This is to support the automation of 'exit' signals on a layout
# A 'sig_passed' callback event will be generated when the signal is overriden if
# and only if a start delay (> 0) is specified. For each subsequent aspect change
# a'sig_updated' callback event will be generated
# -------------------------------------------------------------------------

def trigger_timed_signal (sig_id:int,start_delay:int=0,time_delay:int=5):

    # Validate the signal exists
    if not signals_common.sig_exists(sig_id):
        print ("ERROR: trigger_timed_signal - Signal "+str(sig_id)+" does not exist")
        
    else:
        # get the signal that we are interested in
        signal = signals_common.signals[str(sig_id)]
        
        # Call the signal type-specific functions to trigger the signal
        if signal["sigtype"] == sig_type.colour_light:
            signals_colour_lights.trigger_timed_colour_light_signal (sig_id,start_delay,time_delay)
            
    return()


##########################################################################################
