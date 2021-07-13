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
            trigger_timed_signal (5,0,5)
            clear_section_occupied(5)
        elif item_id == 6:
            trigger_timed_signal (6,0,5)
            clear_section_occupied(4)
                        
    #--------------------------------------------------------------
    # Override signals based on track occupancy
    #--------------------------------------------------------------
                
    if ( (point_switched(1) and section_occupied(5))or
          (not point_switched(1) and section_occupied(4)) ):
        set_signal_override(4)
    else:
        clear_signal_override(4)
        
    if section_occupied(3):
        set_signal_override(3)
    else:
        clear_signal_override(3)

    if section_occupied(2):
        set_signal_override(2)
    else:
        clear_signal_override(2)
    # Also Override the distant signal if any home signals ahead are set to DANGER
    if (section_occupied(1) or not signal_clear(2) or signal_overridden(2)
            or point_switched(1) and (not signal_clear(5) or signal_overridden(5))
            or not point_switched(1) and (not signal_clear(6) or signal_overridden(6))
            or not signal_clear(3) or signal_overridden(3) or not signal_clear(4) or signal_overridden(4) ):
        set_signal_override(1)
    else:
        clear_signal_override(1)

    #--------------------------------------------------------------
    # Refresh Signal 4 based on the route settings
    #--------------------------------------------------------------
    
    if point_switched(1):
        set_route(4,route=route_type.LH1)
    else:
        set_route(4,route=route_type.MAIN)
    
    #-------------------------------------------------------------- 
    # Process the signal/point interlocking
    #--------------------------------------------------------------
    
    # Signal 4 is locked if the FPL for Point 1 is not active
    if not fpl_active(1):
        lock_signal(4)
    else:
        unlock_signal(4)
    # Point 1 is locked if Signal 4 is clear
    if signal_clear(4):
        lock_point(1)
    else:
        unlock_point(1)

    #-------------------------------------------------------------- 
    # Here is the approach control code - this simulates/automates a series of
    # of signals within a block section (e.g. outer home, inner home, starter,
    # advanced starter etc). In this scenario, the distant and home signals
    # should not be cleared for an approaching train if a subsequent home signal
    # is set to DANGER. The signalman would instead set the distant signal to
    # CAUTION and each home preceding home signal to DANGER in order to slow
    # down the approaching train. As the train approaches each home signal the
    # signal would be cleared to enable the train to continue (at low speed)
    # towards the next home signal
    #--------------------------------------------------------------

    if callback_type in (sig_callback_type.sig_switched, sig_callback_type.sig_updated,
                            sig_callback_type.sig_passed, section_callback_type.section_switched):
        if point_switched(1):
            if ( signal_clear(5) and not signal_overridden(5)
                  and signal_clear(4) and not signal_overridden(4)
                    and signal_clear(3) and not signal_overridden(3) ):
                clear_approach_control(4)
                clear_approach_control(3)
                clear_approach_control(2)
            elif not signal_clear(5) or signal_overridden(5):
                set_approach_control(4)
                set_approach_control(3)
                set_approach_control(2)
            elif not signal_clear(4) or signal_overridden(4):
                clear_approach_control(4)
                set_approach_control(3)
                set_approach_control(2)
            elif not signal_clear(3) or signal_overridden(3):
                clear_approach_control(4)
                clear_approach_control(3)
                set_approach_control(2)
        else:
            if (signal_clear(6) and not signal_overridden(6)
                and signal_clear(4) and not signal_overridden(4)
                  and signal_clear(3) and not signal_overridden(3) ):
                clear_approach_control(4)
                clear_approach_control(3)
                clear_approach_control(2)
            elif not signal_clear(6) or signal_overridden(6):
                set_approach_control(4)
                set_approach_control(3)
                set_approach_control(2)
            elif not signal_clear(4) or signal_overridden(4):
                clear_approach_control(4)
                set_approach_control(3)
                set_approach_control(2)
            elif not signal_clear(3) or signal_overridden(3):
                clear_approach_control(4)
                clear_approach_control(3)
                set_approach_control(2)
        
    return()

#------------------------------------------------------------------------------------
# This is where the code begins
#------------------------------------------------------------------------------------

# Create the Window and canvas
print ("Creating Window and Canvas")
window = Tk()
window.title("An example of using Approach Control for Semaphores")
canvas = Canvas(window,height=400,width=1100,bg="grey85")
canvas.pack()

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

print ("Creating the track Occupancy Sections")

# Create the track occupancy sections for the top line
create_section(canvas,1,175,200,section_callback=main_callback_function)
create_section(canvas,2,400,200,section_callback=main_callback_function)
create_section(canvas,3,625,200,section_callback=main_callback_function)
create_section(canvas,4,925,200,section_callback=main_callback_function)
create_section(canvas,5,925,150,section_callback=main_callback_function)

print ("Creating Signals")

# Create the Signals for the top line
create_semaphore_signal (canvas,1,50,200, distant = True,
                            sig_callback=main_callback_function,
                            sig_passed_button = True)
create_semaphore_signal (canvas,2,275,200,
                            sig_callback=main_callback_function,
                            approach_release_button = True,
                            sig_passed_button = True)
create_semaphore_signal (canvas,3,500,200,
                            sig_callback=main_callback_function,
                            approach_release_button = True,
                            sig_passed_button = True)
create_semaphore_signal (canvas,4,725,200,
                            sig_callback=main_callback_function,
                            sig_passed_button = True,
                            approach_release_button = True,
                            lhroute1 = True)
create_semaphore_signal (canvas,5,1000,150,
                            sig_callback=main_callback_function,
                            sig_passed_button=True)
create_semaphore_signal (canvas,6,1000,200,
                            sig_callback=main_callback_function,
                            sig_passed_button=True)

print ("Setting Initial Route and Interlocking")
set_route (4,route=route_type.MAIN)
set_signal_override(1)
set_approach_control(2)
set_approach_control(3)
set_approach_control(4)

# Now enter the main event loop and wait for a button press (which will trigger a callback)
print ("Entering Main Event Loop")
window.mainloop()
