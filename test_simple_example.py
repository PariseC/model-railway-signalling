#----------------------------------------------------------------------
# This programme provides a simple example of how to use the "points"
# and "signals" modules, with the tkinter graphics library to create a
# track schematic with a couple of points, add signals and then apply
# a basic "interlocking" scheme. For a more complicated example (with
# "track circuits", automatic signals and route displays see "my_layout"
# ---------------------------------------------------------------------

from tkinter import *
from model_railway_signals import *
import logging

#----------------------------------------------------------------------
# Here is where we configure the logging - to see what's going on 
#----------------------------------------------------------------------

# Here we configure logging to report the log level and the associated log message
# generated by the code. If you include ':%(funcName)s' in the format string then
# the log message will additionally tell you the function that generated the message
# The default level (no 'level' specified) will provide just warnings and errors
# A level of 'INFO' will tell you what the various 'model_railway_signalling' functions
# are doing 'under the hood' - useful when developing/debugging a layout signalling
# A level of 'DEBUG' will additionally report the DCC Bus commands being sent to the Pi-SPROG
logging.basicConfig(format='%(levelname)s: %(message)s',level=logging.DEBUG) 

# There is an additional level of debug logging that can be enabled for the Pi-SPROG interface
# This will show the actual 'CBUS Grid Connect' protocol commands being sent and received
# Useful for comparing with the console output in the JMRI application for advanced debugging
# Note that the main logging level also needs to be set to DEBUG to generate these messages
debug_dcc = True

#----------------------------------------------------------------------
# This is the main callback function for when something changes
# i.e. a point or signal "button" has been clicked on the display
#----------------------------------------------------------------------

def main_callback_function(item_id,callback_type):

    print ("Callback into main program - Item: "+str(item_id)+" - Callback Type: "+str(callback_type))
    #--------------------------------------------------------------
    # Deal with changes to the Track Occupancy
    #--------------------------------------------------------------
        
    # First deal with the track occupancy
    if (callback_type == sig_callback_type.sig_passed):
        if item_id == 1:
            set_section_occupied(1)
        elif item_id == 2:
            clear_section_occupied(1)
            if point_switched(1):
                set_section_occupied(2)
            else:
                set_section_occupied(3)
        elif item_id == 3:
            clear_section_occupied(2)
            set_section_occupied(4)
        elif item_id == 4:
            clear_section_occupied(3)
            set_section_occupied(4)
        elif item_id == 5:
            trigger_timed_signal (5,0,3)
            clear_section_occupied(4)
            
    #--------------------------------------------------------------
    # Override signals based on track occupancy - we could use
    # the signal passed events to do this but we also need to
    # allow for manual setting/resetting the track occupancy sections
    #--------------------------------------------------------------
    
    if section_occupied(1):
        set_signal_override(1)
    else:
        clear_signal_override(1)
    if ((section_occupied(2) and point_switched(1)) or
            (section_occupied(3) and not point_switched(1))):
        set_signal_override(2)
    else:
        clear_signal_override(2)
    if section_occupied(4):
        set_signal_override(3)
        set_signal_override(4)
    else:
        clear_signal_override(3)
        clear_signal_override(4)

    #--------------------------------------------------------------
    # Refresh the signal aspects based on the route settings
    # The order is important - Need to work back along the route
    #--------------------------------------------------------------
    
    update_signal(3, sig_ahead_id = 5 )
    update_signal(4, sig_ahead_id = 5)
    
    if point_switched(1):
        set_route(2,route=route_type.LH1)
        update_signal(2,sig_ahead_id=3)
    else:
        set_route(2,route=route_type.MAIN)
        update_signal(2,sig_ahead_id=4)

    update_signal(1, sig_ahead_id=2)
    
    #-------------------------------------------------------------- 
    # Process the signal/point interlocking
    #--------------------------------------------------------------
    
    # Signal 2 is locked (at danger) if the point 1 facing point lock is not active
    # We also interlock the subsidary with the main signal aspect
    if not fpl_active(1):
        lock_signal(2)
        lock_subsidary(2)
    else:
        if signal_clear(2): lock_subsidary(2)
        else: unlock_subsidary(2)
        if subsidary_clear(2): lock_signal(2)
        else: unlock_signal(2)
    # Signal 3 is locked (at danger) if point 2 is set against it 
    if not point_switched(2):
        lock_signal(3)
    else:
        unlock_signal(3)
    # Signal 4 is locked (at danger) if point 2 is set against it 
    if point_switched(2):
        lock_signal(4)
    else:
        unlock_signal(4)
    # Point 1 is locked if signal 2 (or its subsidary) is set to clear
    if signal_clear(2) or subsidary_clear(2):
        lock_point(1)
    else:
        unlock_point(1)
    # Point 2 is locked if either signals 3 or 4 are set to clear
    if signal_clear(3) or signal_clear(4):
        lock_point(2)
    else:
        unlock_point(2)
        
    return()

#------------------------------------------------------------------------------------
# This is where the code begins
#------------------------------------------------------------------------------------

# Create the Window and canvas
print ("Creating Window and Canvas")
window = Tk()
window.title("Simple Interlocking Example")
canvas = Canvas(window,height=400,width=1000,bg="grey85")
canvas.pack()

# Initialise the Pi-SPROG-3 and define the DCC mappings for the signals and points we are
# going to create (if not running on a Pi-SPROG this will generate an error message, but
# the software will still work albeit without sending any DCC Commands to the Pi-SPROG)
# Mappings should be created first so that when the signals and points are created then
# the appropriate DCC bus commands will be sent to set the initial aspects correctly

print ("Initialising Pi Sprog and creating DCC Mappings")
initialise_pi_sprog (dcc_debug_mode=debug_dcc)
request_dcc_power_on()

# Signal 2 assumes a Signalist SC1 decoder with a base address of 1 (CV1=5)
# and set to "8 individual output" Mode (CV38=8). In this example we are using
# outputs A,B,C,D to drive our signal with E driving the feather indication and
# F driving the "Calling On" Subsidary aspect
# The Signallist SC1 uses 8 consecutive addresses in total (which equate to DCC
# addresses 1 to 8 for this example) - but we only need to use the first 6
map_dcc_signal (sig_id = 2,
                danger = [[1,True],[2,False],[3,False],[4,False]],
                proceed = [[1,False],[2,True],[3,False],[4,False]],
                caution = [[1,False],[2,False],[3,True],[4,False]],
                prelim_caution = [[1,False],[2,False],[3,True],[4,True]],
                LH1 = [[5,True]], NONE = [[5,False]],
                subsidary = 6)

# Signals 1,3,4 and 5 assume a TrainTech DCC 4 Aspect Signal - these are event driven
# and can take up to 4 consecutive addresses (if you include the flashing aspects)

# Signal 1 (addresses 22,23,24,25) - uses the simplified traintech signal mapping function
map_traintech_signal (sig_id = 1, base_address = 22)
# Signal 3 (addresses 9,10,11,12) - uses the simplified traintech signal mapping function
map_traintech_signal (sig_id = 3, base_address = 9)
# Signal 4 (addresses 13,14,15,16) - uses the simplified traintech signal mapping function
map_traintech_signal (sig_id = 4, base_address = 13)

# Signal 5 (addresses 17,18,19,20) shows you how a TrainTech signal mapping is configured "under the hood"
# note that if it had a route indication you should also include 'auto_route_inhibit = True' as TrainTech
# signals automatically inhibit the feather when the signal is set to DANGER
map_dcc_signal (sig_id = 5,
                danger = [[17,False]],
                proceed = [[17,True]],
                caution = [[18,True]],
                prelim_caution = [[18,False]])

# Points are simply mapped to single addresses
map_dcc_point (1, 100)
map_dcc_point (2, 101)

print ("Drawing Schematic and creating points")
# Draw the the Main line (up to the first point)
canvas.create_line(0,200,350,200,fill="black",width=3) 
# Create (and draw) the first point - a left hand point with a Facing Point Lock
# The "callback" is the name of the function (above) that will be called when something has changed
create_point(canvas,1,point_type.LH, 375,200,"black",point_callback=main_callback_function,fpl=True) 
# Draw the Main Line and Loop Line
canvas.create_line(375,175,400,150,fill="black",width=3) # 45 degree line from point to start of loop
canvas.create_line(400,150,675,150,fill="black",width=3) # Loop line
canvas.create_line(400,200,675,200,fill="black",width=3) # Main Line
canvas.create_line(675,150,700,175,fill="black",width=3) # 45 degree line from end of loop to second point
# Create (and draw) the second point - a right hand point rotated by 180 degrees
# No facing point lock needed for this point as direction of travel is left to right
create_point(canvas,2,point_type.RH, 700,200,"black",point_callback=main_callback_function,orientation=180) 
# Draw the continuation of the Main Line 
canvas.create_line(725,200,1000,200,fill="black",width=3) # 45 degree line from point to start of loop

# Create the track occupancy sections
print ("Creating the track Occupancy Sections")
create_section (canvas,1,175,200,section_callback = main_callback_function)
create_section (canvas,2,500,150,section_callback = main_callback_function)
create_section (canvas,3,500,200,section_callback = main_callback_function)
create_section (canvas,4,800,200,section_callback = main_callback_function)

# Create the Signals on the Schematic track plan
# The "callback" is the name of the function (above) that will be called when something has changed
# Signal 2 is the signal just before the point - so it needs a route indication
print ("Creating Signals")
create_colour_light_signal (canvas, 1, 50, 200,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback = main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False)
create_colour_light_signal (canvas, 2, 275, 200,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback = main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False,
                            position_light = True,
                            lhfeather45 = True)
create_colour_light_signal (canvas, 3, 600, 150,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback = main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False)
create_colour_light_signal (canvas, 4, 600, 200,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback = main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False)
create_colour_light_signal (canvas, 5, 900, 200,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback = main_callback_function,
                            fully_automatic = True,
                            sig_passed_button = True)

# Map external track sensors for the signals - For simplicity, we'll give them the same ID as the signal
# We'll also map them to the associated "signal passed" events rather than using their own callback
print ("Creating external Track Sensor Mappings")
create_track_sensor (1, gpio_channel = 4, signal_passed = 1)
create_track_sensor (2, gpio_channel = 5, signal_passed = 2)
create_track_sensor (3, gpio_channel = 6, signal_passed = 3)
create_track_sensor (4, gpio_channel = 7, signal_passed = 4)
create_track_sensor (5, gpio_channel = 8, signal_passed = 5)

# Set the initial interlocking conditions - in this case lock signal 3 as point 2 is set against it
print ("Setting Initial Interlocking")
lock_signal(3)

# Now enter the main event loop and wait for a button press (which will trigger a callback)
print ("Entering Main Event Loop")
window.mainloop()
