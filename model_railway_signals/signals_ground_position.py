# --------------------------------------------------------------------------------
# This module is used for creating and managing Ground Position Light signal objects
#
# Currently supported sub-types :
#       - Groud position light  
#           - Early - red/white / white/white
#           - Modern (post 1996) - red/red / white /white
#       - Shunt Ahead position light
#           - Early - yellow/white / white/white
#           - Modern (post 1996) yellow/yellow / white /white
#
# Common features supported by Ground Position Colour Light signals
#           - lock_signal / unlock_signal
#           - set_signal_override / clear_signal_override
# --------------------------------------------------------------------------------

from . import signals_common
from . import dcc_control
from . import mqtt_interface
from . import file_interface
from . import common

from tkinter import *
import logging

# -------------------------------------------------------------------------
# Externally called function to create a Ground Position Signal (drawing objects
# + state). By default the Signal is "NOT CLEAR" (i.e. set to DANGER)
# All attributes (that need to be tracked) are stored as a dictionary
# This is then added to a dictionary of Signals for later reference
# -------------------------------------------------------------------------

def create_ground_position_signal (canvas, sig_id:int, x:int, y:int,
                                    sig_callback = None,
                                    orientation:int = 0,
                                    sig_passed_button: bool = False, 
                                    shunt_ahead: bool = False,
                                    modern_type: bool = False):
    global logging

    logging.info ("Signal "+str(sig_id)+": Creating Ground Position Signal")
    # Do some basic validation on the parameters we have been given
    if signals_common.sig_exists(sig_id):
        logging.error ("Signal "+str(sig_id)+": Signal already exists")        
    elif sig_id < 1:
        logging.error ("Signal "+str(sig_id)+": Signal ID must be greater than zero")        
    elif orientation != 0 and orientation != 180:
        logging.error ("Signal "+str(sig_id)+": Invalid orientation angle - only 0 and 180 currently supported")                  
    else:  
        
        # Draw the signal base
        canvas.create_line (common.rotate_line (x,y,0,0,0,-25,orientation),width=2)
        # Draw the main body of signal
        point_coords1 = common.rotate_point (x,y,0,-5,orientation) 
        point_coords2 = common.rotate_point (x,y,0,-25,orientation) 
        point_coords3 = common.rotate_point (x,y,+20,-25,orientation) 
        point_coords4 = common.rotate_point (x,y,+20,-20,orientation) 
        point_coords5 = common.rotate_point (x,y,+5,-5,orientation) 
        points = point_coords1, point_coords2, point_coords3, point_coords4, point_coords5
        canvas.create_polygon (points, outline="black")
        # Create the position light "dark" aspects (i.e. when particular aspect is "not-lit")
        # We don't need to create a "dark" aspect for the "root" position light as this is always lit
        canvas.create_oval (common.rotate_line (x,y,+9,-24,+16,-17,orientation),fill="grey",outline="black")
        canvas.create_oval (common.rotate_line (x,y,+1,-24,+8,-17,orientation),fill="grey",outline="black")
        # Draw the "DANGER" and "PROCEED" aspects (initially hidden)
        if shunt_ahead: danger_colour = "gold"
        else: danger_colour = "red"
        if modern_type: root_colour = danger_colour
        else: root_colour = "white"
        sigoff1 = canvas.create_oval (common.rotate_line (x,y,+1,-14,+8,-7,orientation),fill="white",outline="black",state="hidden")
        sigoff2 = canvas.create_oval (common.rotate_line (x,y,+9,-24,+16,-17,orientation),fill="white",outline="black",state="hidden")
        sigon1 = canvas.create_oval (common.rotate_line (x,y,+1,-14,+8,-7,orientation),fill=root_colour,outline="black",state="hidden")
        sigon2 = canvas.create_oval (common.rotate_line (x,y,+1,-24,+8,-17,orientation),fill=danger_colour,outline="black",state="hidden")

        # Create all of the signal elements common to all signal types
        signals_common.create_common_signal_elements (canvas, sig_id, x, y,
                                       signal_type = signals_common.sig_type.ground_position,
                                       ext_callback = sig_callback,
                                       orientation = orientation,
                                       sig_passed_button = sig_passed_button)
        
        # Add all of the signal-specific elements we need to manage Ground Position light signal types
        signals_common.signals[str(sig_id)]["sigoff1"]  = sigoff1         # Type-specific - drawing object
        signals_common.signals[str(sig_id)]["sigoff2"]  = sigoff2         # Type-specific - drawing object
        signals_common.signals[str(sig_id)]["sigon1"]   = sigon1          # Type-specific - drawing object
        signals_common.signals[str(sig_id)]["sigon2"]   = sigon2          # Type-specific - drawing object
        
        # Get the initial state for the signal (if layout state has been successfully loaded)
        # if nothing has been loaded then the default state (as created) will be applied
        load_sigclear,load_subclear,load_relonred,load_relonyel = file_interface.get_initial_signal_state(sig_id)
        # Toggle the signal state if SWITCHED (loaded_state_sigclear will be 'None' if no data was loaded)
        # Note that toggling the signal will set the signal on the schematic to the correct initial aspect
        # and send the appropriate DCC commands to set the aspect of the external signal accordingly.
        # Otherwise we need to update the signal to set the initial aspect and send out the DCC commands
        if load_sigclear: signals_common.toggle_signal(sig_id)
        else: update_ground_position_signal (sig_id)
       
    return ()

# -------------------------------------------------------------------------
# Internal function to Refresh the aspects of a ground position signal
# Function assumes the Sig_ID has been validated by the calling module
# Note that we expect this function to only ever get called on a state 
# change therefore we don't track the displayed aspect of the signal
# -------------------------------------------------------------------------

def update_ground_position_signal (sig_id:int):

    global logging
    
    # Establish what the signal should be displaying based on the state
    if not signals_common.signals[str(sig_id)]["sigclear"]:   
        aspect_to_set = signals_common.signal_state_type.DANGER
        log_message = " (signal is ON)"
    elif signals_common.signals[str(sig_id)]["override"]:
        aspect_to_set = signals_common.signal_state_type.DANGER
        log_message = " (signal is OVERRIDDEN)"
    else:
        aspect_to_set = signals_common.signal_state_type.PROCEED
        log_message = " (signal is OFF)"
        
    # Only refresh the signal if the aspect has been changed
    if aspect_to_set != signals_common.signals[str(sig_id)]["sigstate"]:
        logging.info ("Signal "+str(sig_id)+": Changing aspect to " + str(aspect_to_set).rpartition('.')[-1] + log_message)
        signals_common.signals[str(sig_id)]["sigstate"] = aspect_to_set

        if signals_common.signals[str(sig_id)]["sigstate"] == signals_common.signal_state_type.PROCEED:
            signals_common.signals[str(sig_id)]["canvas"].itemconfig(signals_common.signals[str(sig_id)]["sigoff1"],state="normal")
            signals_common.signals[str(sig_id)]["canvas"].itemconfig(signals_common.signals[str(sig_id)]["sigoff2"],state="normal")
            signals_common.signals[str(sig_id)]["canvas"].itemconfig(signals_common.signals[str(sig_id)]["sigon1"],state="hidden")
            signals_common.signals[str(sig_id)]["canvas"].itemconfig(signals_common.signals[str(sig_id)]["sigon2"],state="hidden")

        elif signals_common.signals[str(sig_id)]["sigstate"] == signals_common.signal_state_type.DANGER:
            signals_common.signals[str(sig_id)]["canvas"].itemconfig(signals_common.signals[str(sig_id)]["sigoff1"],state="hidden")
            signals_common.signals[str(sig_id)]["canvas"].itemconfig(signals_common.signals[str(sig_id)]["sigoff2"],state="hidden")
            signals_common.signals[str(sig_id)]["canvas"].itemconfig(signals_common.signals[str(sig_id)]["sigon1"],state="normal")
            signals_common.signals[str(sig_id)]["canvas"].itemconfig(signals_common.signals[str(sig_id)]["sigon2"],state="normal")
            
        # Send the required DCC bus commands to change the signal to the desired aspect. Note that commands will only
        # be sent if the Pi-SPROG interface has been successfully configured and a DCC mapping exists for the signal
        dcc_control.update_dcc_signal_aspects(sig_id)
        
        # Publish the signal changes to the broker (for other nodes to consume). Note that state changes will only
        # be published if the MQTT interface has been successfully configured for publishing updates for this signal
        mqtt_interface.publish_signal_state(sig_id)            
        
    return ()

###############################################################################
