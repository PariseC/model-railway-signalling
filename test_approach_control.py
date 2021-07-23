#----------------------------------------------------------------------
# This programme provides a simple example of how to use "approach control"
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
debug_dcc = False

#----------------------------------------------------------------------
# This is the main callback function for when something changes
# i.e. a point or signal "button" has been clicked on the display
#----------------------------------------------------------------------

def main_callback_function(item_id,callback_type):

    #--------------------------------------------------------------
    # Deal with changes to the Track Occupancy
    #--------------------------------------------------------------
        
    if callback_type == sig_callback_type.sig_passed:
        if item_id == 1:
            set_section_occupied(1)
        elif item_id == 2:
            clear_section_occupied(1)
            set_section_occupied(2)
        elif item_id == 3:
            clear_section_occupied(2)
            set_section_occupied(3)
        elif item_id == 4:
            clear_section_occupied(3)
            if point_switched(1):
                set_section_occupied(5)
            else:
                set_section_occupied(4)
        elif item_id == 5:
            trigger_timed_signal (5,0,3)
            clear_section_occupied(5)
        elif item_id == 6:
            trigger_timed_signal (6,0,3)
            clear_section_occupied(4)
            
        if item_id == 11:
            set_section_occupied(11)
        elif item_id == 12:
            clear_section_occupied(11)
            set_section_occupied(12)
        elif item_id == 13:
            clear_section_occupied(12)
            set_section_occupied(13)
        elif item_id == 14:
            clear_section_occupied(13)
            if point_switched(11):
                set_section_occupied(15)
            else:
                set_section_occupied(14)
        elif item_id == 15:
            trigger_timed_signal (15,0,3)
            clear_section_occupied(15)
        elif item_id == 16:
            trigger_timed_signal (16,0,3)
            clear_section_occupied(14)
            
    #--------------------------------------------------------------
    # Override signals based on track occupancy - we could use
    # the signal passed events to do this but we also need to
    # allow for manual setting/resetting the track occupancy sections
    #--------------------------------------------------------------
    
    for I in (1,2,3,11,12,13):
        if section_occupied(I):
            set_signal_override(I)
        else:
            clear_signal_override(I)
    if (point_switched(1) and section_occupied(5)) or (not point_switched(1) and section_occupied(4)):
        set_signal_override(4)
    else:
        clear_signal_override(4)
    if (point_switched(11) and section_occupied(15)) or (not point_switched(11) and section_occupied(14)):
        set_signal_override(14)
    else:
        clear_signal_override(14)

    #--------------------------------------------------------------
    # Refresh the signal aspects based on the route settings
    # The order is important - Need to work back along the route
    #--------------------------------------------------------------
    
    if point_switched(1):
        set_route(4,route=route_type.LH1)
        update_signal(4,sig_ahead_id=5)
    else:
        set_route(4,route=route_type.MAIN)
        update_signal(4,sig_ahead_id=6)
    update_signal(3,sig_ahead_id=4)
    update_signal(2,sig_ahead_id=3)
    update_signal(1,sig_ahead_id=2)
    
    if point_switched(11):
        set_route(14,theatre_text="1")
        update_signal(14,sig_ahead_id=15)
    else:
        set_route(14,theatre_text="2")
        update_signal(14,sig_ahead_id=16)
    update_signal(13,sig_ahead_id=14)
    update_signal(12,sig_ahead_id=13)
    update_signal(11,sig_ahead_id=12)

    #-------------------------------------------------------------- 
    # Process the signal/point interlocking
    #--------------------------------------------------------------
    
    if not fpl_active(1):
        lock_signal(4)
    else:
        unlock_signal(4)
    if signal_clear(4):
        lock_point(1)
    else:
        unlock_point(1)
    if not fpl_active(11):
        lock_signal(14)
    else:
        unlock_signal(14)
    if signal_clear(14):
        lock_point(11)
    else:
        unlock_point(11)

    #-------------------------------------------------------------- 
    # Here is the approach control code - we only want to set approach
    # control when the route is initially set up - and then re-set the
    # approach control when the signal is passed. this is so we don't
    # inadvertantly re-set the approach control on other events received
    # between the time the train releases the approach control and the
    # train actually reaches the signal. We'll also clear the approach
    # control if the route is switched back to main
    #--------------------------------------------------------------

    if ((callback_type == point_callback_type.point_switched and item_id==1 and point_switched(1)) or
          (callback_type == sig_callback_type.sig_passed and item_id==4 and point_switched(1)) ):
        set_approach_control (4,release_on_yellow=True)
    if callback_type == point_callback_type.point_switched and item_id==1 and not point_switched(1):
        clear_approach_control (4)

    if ( (callback_type == point_callback_type.point_switched and item_id==11 and point_switched(11)) or
           (callback_type == sig_callback_type.sig_passed and item_id==14 and point_switched(11)) ):
        set_approach_control (14,release_on_yellow=False)
    if callback_type == point_callback_type.point_switched and item_id==11 and not point_switched(11):
        clear_approach_control (14)
        
    return()

#------------------------------------------------------------------------------------
# This is where the code begins
#------------------------------------------------------------------------------------

# Create the Window and canvas
print ("Creating Window and Canvas")
window = Tk()
window.title("An example of using Approach Control")
canvas = Canvas(window,height=600,width=1100,bg="grey85")
canvas.pack()

# Initialise the Pi-SPROG-3 and define the DCC mappings for the signals and points we are
# going to create (if not running on a Pi-SPROG this will generate an error message, but
# the software will still work albeit without sending any DCC Commands to the Pi-SPROG)
# Mappings should be created first so that when the signals and points are created then
# the appropriate DCC bus commands will be sent to set the initial aspects correctly

print ("Initialising Pi Sprog and creating DCC Mappings")
initialise_pi_sprog (dcc_debug_mode=debug_dcc)
request_dcc_power_on()

# Signals 2, 3 and 4 are configured to drive TrainTech DCC Signals. These use up to 4
# DCC addresses - Base, Base+1, Base+2 & Base+3 (plus another address anywhere in the DCC
# address space for a Feather or Theatre route indicator)

# Signal 2 (addresses 9,10,11,12) shows you how a TrainTech signal is mapped "under the hood"
# Note that Signals 2 assumes the TrainTech 4 aspect varient which support flashing aspects
# These are event driven signals - so we only need a single command to change the aspect
# Note that if it was a signal with a route indication you would set 'auto_route_inhibit = True'
map_dcc_signal (sig_id = 2,
                danger = [[9,False]],
                proceed = [[9,True]],
                caution = [[10,True]],
                prelim_caution = [[10,False]],
                flash_caution = [[12,True]],
                flash_prelim_caution = [[12,False]])

# Signal 3 (addresses 13,14,15,16) - uses the simplified Train_Tech signal mapping function
# Note that Signals 3 assumes the TrainTech 4 aspect varient which support flashing aspects
map_traintech_signal (sig_id = 3, base_address = 13)

# Signal 4 (addresses 17,18,19,20)- a traintech 4 aspect with a feather (address 21)
# Note that you could also just programme the Route Indication to use the same address as point 1
# and not bother mapping the route indication at all - this would be fine as the traintech signals
# automatically inhibit the route indication when the signal is set to RED
map_traintech_signal (sig_id = 4, base_address = 17, route_address = 21, feather_route= route_type.LH1)

# Signal 14 assumes a Signalist SC1 decoder with a base address of 1 (CV1=5)
# and set to "8 individual output" Mode (CV38=8). In this example we are using
# outputs A,B,C,D to drive our signal with E & F driving the feather indications
# The Signallist SC1 uses 8 consecutive addresses in total (which equate to DCC
# addresses 1 to 8 for this example) - but we only need to use the first 6
map_dcc_signal (sig_id = 14,
                danger = [[1,True],[2,False],[3,False],[4,False]],
                proceed = [[1,False],[2,True],[3,False],[4,False]],
                caution = [[1,False],[2,False],[3,True],[4,False]],
                prelim_caution = [[1,False],[2,False],[3,True],[4,True]],
                THEATRE = [ ["#",[[5,False],[6,False]]],
                            ["1",[[6,False],[5,True]]],
                            ["2",[[5,False],[6,True]]]  ] )

print ("Drawing Schematic and creating points")

# Draw the the Top line (up to the first point)
canvas.create_line(0,200,800,200,fill="black",width=3) 
# Create (and draw) the first point - a left hand point with a Facing Point Lock
# The "callback" is the name of the function (above) that will be called when something has changed
create_point(canvas,1,point_type.LH, 825,200,"black",point_callback=main_callback_function,fpl=True) 
# Draw the Main Line and Loop Line
canvas.create_line(825,175,850,150,fill="black",width=3) # 45 degree line from point to start of loop
canvas.create_line(850,150,1100,150,fill="black",width=3) # Loop line
canvas.create_line(850,200,1100,200,fill="black",width=3) # Main Line

# Draw the the Bottom line (up to the first point)
canvas.create_line(0,400,810,400,fill="black",width=3) 
# Create (and draw) the first point - a left hand point with a Facing Point Lock
# The "callback" is the name of the function (above) that will be called when something has changed
create_point(canvas,11,point_type.LH, 835,400,"black",point_callback=main_callback_function,fpl=True) 
# Draw the Main Line and Loop Line
canvas.create_line(835,375,860,350,fill="black",width=3) # 45 degree line from point to start of loop
canvas.create_line(860,350,1100,350,fill="black",width=3) # Loop line
canvas.create_line(860,400,1100,400,fill="black",width=3) # Main Line

print ("Creating the track Occupancy Sections")

# Create the track occupancy sections for the top line
create_section(canvas,1,175,200,section_callback=main_callback_function)
create_section(canvas,2,400,200,section_callback=main_callback_function)
create_section(canvas,3,625,200,section_callback=main_callback_function)
create_section(canvas,4,925,200,section_callback=main_callback_function)
create_section(canvas,5,925,150,section_callback=main_callback_function)

# Create the track occupancy sections for the top line
create_section(canvas,11,175,400,section_callback=main_callback_function)
create_section(canvas,12,400,400,section_callback=main_callback_function)
create_section(canvas,13,625,400,section_callback=main_callback_function)
create_section(canvas,14,925,400,section_callback=main_callback_function)
create_section(canvas,15,925,350,section_callback=main_callback_function)

print ("Creating Signals")

# Create the Signals for the top line
create_colour_light_signal (canvas,1,50,200,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback=main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False)
create_colour_light_signal (canvas,2,275,200,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback=main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False)
create_colour_light_signal (canvas,3,500,200,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback=main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False)
create_colour_light_signal (canvas,4,725,200,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback=main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False,
                            approach_release_button = True,
                            lhfeather45 = True)
create_colour_light_signal (canvas,5,1000,150,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback=main_callback_function,
                            fully_automatic=True,
                            sig_passed_button=True)
create_colour_light_signal (canvas,6,1000,200,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback=main_callback_function,
                            fully_automatic=True,
                            sig_passed_button=True)

# Create the Signals for the bottom line
create_colour_light_signal (canvas,11,50,400,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback=main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False)
create_colour_light_signal (canvas,12,275,400,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback=main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False)
create_colour_light_signal (canvas,13,500,400,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback=main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False)
create_colour_light_signal (canvas,14,725,400,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback=main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False,
                            approach_release_button = True,
                            theatre_route_indicator = True)
create_colour_light_signal (canvas,15,1000,350,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback=main_callback_function,
                            fully_automatic=True,
                            sig_passed_button=True)
create_colour_light_signal (canvas,16,1000,400,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback=main_callback_function,
                            fully_automatic=True,
                            sig_passed_button=True)

print ("Setting Initial Route and Interlocking")
set_route (4,route=route_type.MAIN)
set_route (14,theatre_text="2")

# Now enter the main event loop and wait for a button press (which will trigger a callback)
print ("Entering Main Event Loop")
window.mainloop()
