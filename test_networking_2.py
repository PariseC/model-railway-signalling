#----------------------------------------------------------------------
# This programme provides an example of how to use the MQTT Networking functions
# to link different applications (representing different"signal boxes") together
# This is "Box2" - A remote node forwarding all DCC commands to "Box1"
# ---------------------------------------------------------------------

from tkinter import *
from model_railway_signals import *
import logging

#----------------------------------------------------------------------
# Configure the log level. If no 'level' is specified specified only warnings and errors
# will be generated. A level of 'INFO' will tell you what the various functions are doing
# 'under the hood' - useful when developing/debugging a layout signalling Scheme. A level
# of 'DEBUG' will additionally report the DCC Bus commands being sent to the Pi-SPROG and
# the messages being published to external nodes via the MQTT Broker
#----------------------------------------------------------------------

logging.basicConfig(format='%(levelname)s: %(message)s',level=logging.DEBUG)

# There is an additional level of debug logging that can be enabled for the MQTT interface
# This will show the log messages being generated by the Client for published/received messages
# Note that the main logging level also needs to be set to DEBUG to generate these messages

mqtt_debug = False

#----------------------------------------------------------------------
# This is the main callback function (to process change events)
#----------------------------------------------------------------------

def main_callback_function(item_id,callback_type):

    print ("Callback into main program - Item: "+str(item_id)+" - Callback Type: "+str(callback_type))

    # Deal with any EXTERNAL changes to the Track Occupancy. In this case
    if callback_type == section_callback_type.section_updated:
        # We want the local Section 1 to mirror any changes made to Box1 Section 3 
        if item_id == "Box1-3":
            if section_occupied ("Box1-3"):
                set_section_occupied(1,section_occupied ("Box1-3"))
            else:
                clear_section_occupied(1)
        # We want the local Section 12 to mirror any changes made to Box1 Section 10 
        if item_id == "Box1-10":
            if section_occupied ("Box1-10"):
                set_section_occupied(12,section_occupied ("Box1-10"))
            else:
                clear_section_occupied(12)

    # Deal with LOCAL changes to the Track Occupancy (based on signal passed events)
    if callback_type == sig_callback_type.sig_passed:
        # Upper Line
        if item_id == "Box1-3":
            # We could also use external signal passed events to update local section occupancy
            # but its probably more "robust" to use the section updated events as above
            print("Signal Updated event received from Box1-3 - Train entering our section")
        elif item_id == 1:
            set_section_occupied(2,clear_section_occupied(1))
        elif item_id == 2:
            set_section_occupied(3,clear_section_occupied(2))
        elif item_id == 3:
            clear_section_occupied(3)
            trigger_timed_signal(3,0,5)
        # Lower Line
        elif item_id == 10:
            set_section_occupied(10)
        elif item_id == 11:
            set_section_occupied(11,clear_section_occupied(10))
        elif item_id == 12:
            set_section_occupied(12,clear_section_occupied(11))
        elif item_id == "Box1-11":
            clear_section_occupied(12)        
            
    # Override signals based on track occupancy
    # Upper Line
    if section_occupied(2): set_signal_override(1)
    else: clear_signal_override(1)
    if section_occupied(3): set_signal_override(2)
    else: clear_signal_override(2)
    # Lower Line
    if section_occupied(10): set_signal_override(10)
    else: clear_signal_override(10)
    if section_occupied(11): set_signal_override(11)
    else: clear_signal_override(11)
    if section_occupied(12): set_signal_override(12)
    else: clear_signal_override(12)

    # Refresh the signal aspects based on the route settings
    # The order is important - Need to work back along the route
    update_signal(2, sig_ahead_id = 3)
    update_signal(1, sig_ahead_id = 2)
    
    # Update the state of Signal 112 (signal 12 distant arm) to "mirror"
    # the state of Box1 Signal 10 (on the remote network node
    if signal_state("Box1-10") == signal_state_type.PROCEED:
        if not signal_clear(112): toggle_signal(112)
    else:
        if signal_clear(112): toggle_signal(112)

    return()

#------------------------------------------------------------------------------------
# This is where the main code begins
#------------------------------------------------------------------------------------

# Create the Window and canvas
print ("Creating Window and Canvas")
window = Tk()
window.title("Simple Networking Example - Box2 (Remote node)")
canvas = Canvas(window,height=350,width=800,bg="grey85")
canvas.pack()

print ("Creating DCC Mappings for Signals")
# Signals 1,2,3 assume a TrainTech DCC 4 Aspect Signal - these are event driven
# and can take up to 4 consecutive addresses (if you include the flashing aspects)
map_traintech_signal (sig_id = 1, base_address = 40)
map_traintech_signal (sig_id = 2, base_address = 50)
map_traintech_signal (sig_id = 3, base_address = 60)
# Signals 10,11,12 assume a single address mapping for the semaphore arms
map_semaphore_signal (sig_id = 10, main_signal = 104)
map_semaphore_signal (sig_id = 11, main_signal = 105)
map_semaphore_signal (sig_id = 12, main_signal = 106)

print ("Initialising MQTT Client and connecting to external Broker")
# Configure the MQTT Broker networking feature to allow this application node to act as a remote
# DCC command station for other application nodes (i.e. forward received DCC commands to the Pi-Sprog) 
configure_networking(broker_host ="mqtt.eclipseprojects.io", network_identifier="network1",
                     node_identifier= "Box2",publish_dcc_commands=True, mqtt_enhanced_debugging=mqtt_debug)
# Configure the events/updates we want to publish/subscribe to
set_sections_to_publish_state(1,12)
set_signals_to_publish_state(1)
set_signals_to_publish_passed_events(12)
subscribe_to_section_updates("Box1", main_callback_function,3,10)
subscribe_to_signal_updates("Box1", main_callback_function,10)
subscribe_to_signal_passed_events("Box1", main_callback_function,3)
                     
print ("Drawing Layout Schematic")
canvas.create_line(0,100,800,100,fill="black",width=3)
canvas.create_line(0,200,800,200,fill="black",width=3)
canvas.create_text (400,20,text="Signal 1 is configured to publish State Updates and Signal Passed Events (to Box1)")
canvas.create_text (400,40,text="Box2 also subscribes to Signal Passed Events from Box1-3 - to update track occupancy")
canvas.create_text (400,270,text="Signal 12 is configured to publish Signal Passed Events (to Box1)")
canvas.create_text (400,290,text="Box2 subscribes to Signal Passed Events from Box1-11 - to update track occupancy")
canvas.create_text (400,310,text="Box2 subscribes to Signal State Updates from Box1-10 - for Distant Arm of Signal 12")

print ("Creating Track Occupancy Sections")
create_section (canvas,1,75,100,section_callback = main_callback_function)
create_section (canvas,2,325,100,section_callback = main_callback_function)
create_section (canvas,3,575,100,section_callback = main_callback_function)
create_section (canvas,12,75,200,section_callback = main_callback_function)
create_section (canvas,11,325,200,section_callback = main_callback_function)
create_section (canvas,10,575,200,section_callback = main_callback_function)

print ("Creating Signals")
create_colour_light_signal (canvas, 1, 175, 100,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback = main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False)
create_colour_light_signal (canvas, 2, 425, 100,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback = main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False)
create_colour_light_signal (canvas, 3, 675, 100,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback = main_callback_function,
                            sig_passed_button = True,
                            fully_automatic=True)
create_semaphore_signal (canvas, 10, 700, 200,
                        distant = True, orientation = 180,
                        sig_callback = main_callback_function,
                        sig_passed_button = True)
create_semaphore_signal (canvas, 11, 450, 200, orientation = 180,
                        sig_callback = main_callback_function,
                        sig_passed_button = True)
create_semaphore_signal (canvas, 12, 200, 200, orientation = 180,
                        sig_callback = main_callback_function,
                        sig_passed_button = True)
create_semaphore_signal (canvas,112,200,200,
                         orientation = 180, distant = True,
                         fully_automatic = True,
                         associated_home = 12)

print ("Entering Main Event Loop")
window.mainloop()

#############################################################################################
