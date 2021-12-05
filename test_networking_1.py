#----------------------------------------------------------------------
# This programme provides an example of how to use the MQTT Networking functions
# to link different applications (representing different"signal boxes") together
# This is "Box1" - and acting as the main Pi-Sprog interface
# ---------------------------------------------------------------------

from tkinter import *
from model_railway_signals import *
import logging

# Configure the logging - to see what's going on 

logging.basicConfig(format='%(levelname)s: %(message)s',level=logging.DEBUG) 

#----------------------------------------------------------------------
# This is the main callback function for when something changes
#----------------------------------------------------------------------

def main_callback_function(item_id,callback_type):

    print ("Callback into main program - Item: "+str(item_id)+" - Callback Type: "+str(callback_type))

    # Deal with changes to the Track Occupancy
    
    if (callback_type == sig_callback_type.sig_passed):
        if item_id == 1:
            set_section_occupied(1)
        elif item_id == 2:
            clear_section_occupied(1)
            set_section_occupied(2)
        elif item_id == 3:
            clear_section_occupied(2)
            set_section_occupied(3)
        elif item_id == "Box2-1":
            clear_section_occupied(3)
            
        elif item_id == "Box2-12" or item_id == 10:
            set_section_occupied(10)
        elif item_id == 11:
            clear_section_occupied(10)
            set_section_occupied(11)
        elif item_id == 12:
            clear_section_occupied(11)
            set_section_occupied(12)

    # Override signals based on track occupancy
    
    if section_occupied(1):
        set_signal_override(1)
    else:
        clear_signal_override(1)
    if section_occupied(2):
        set_signal_override(2)
    else:
        clear_signal_override(2)
    if section_occupied(3):
        set_signal_override(3)
    else:
        clear_signal_override(3)
        
    if section_occupied(10):
        set_signal_override(10)
    else:
        clear_signal_override(10)
    if section_occupied(11):
        set_signal_override(11)
    else:
        clear_signal_override(11)
    if section_occupied(12):
        set_signal_override(12)
    else:
        clear_signal_override(12)

    # Refresh the signal aspects based on the route settings
    # The order is important - Need to work back along the route

    update_signal(3, sig_ahead_id = "Box2-1")
    update_signal(2, sig_ahead_id = 3)
    update_signal(1, sig_ahead_id = 2)
        
    return()

#------------------------------------------------------------------------------------
# This is where the code begins
#------------------------------------------------------------------------------------

# Create the Window and canvas
print ("Creating Window and Canvas")
window = Tk()
window.title("Simple Networking Example - Box1 (Pi Sprog Node)")
canvas = Canvas(window,height=350,width=750,bg="grey85")
canvas.pack()

canvas.create_text (400,20,text="Box1 subscribes to Signal Passed Events from Box2-1 - to update track occupancy")
canvas.create_text (400,40,text="Box1 also subscribes to Signal State Updates from Box2-1 - to update Signal 3 Aspect")
canvas.create_text (400,150,text="Signal 3 is configured to publish Signal Passed Events (to Box2)")
canvas.create_text (400,270,text="Signal 10 is configured to publish Signal State Updates (to Box2)")
canvas.create_text (400,290,text="Signal 11 is configured to publish Signal Passed Events (to Box2)")
canvas.create_text (400,310,text="Box1 subscribes to Signal Passed Events from Box1-12 - to update track occupancy")

print ("Initialising Pi Sprog and creating DCC Mappings")
initialise_pi_sprog (dcc_debug_mode=False)
request_dcc_power_on()

# Signals 1,2,3,4 assume a TrainTech DCC 4 Aspect Signal - these are event driven
# and can take up to 4 consecutive addresses (if you include the flashing aspects)
map_traintech_signal (sig_id = 1, base_address = 10)
map_traintech_signal (sig_id = 2, base_address = 20)
map_traintech_signal (sig_id = 3, base_address = 30)

print ("Initialising MQTT Client and connecting to external MQTT Message Broker")
# Configure the MQTT Broker networking feature to allow this application node to act as a remote
# DCC command station for other application nodes (i.e. forward received DCC commands to the Pi-Sprog) 
configure_networking(broker_host ="mqtt.eclipseprojects.io", network_identifier="network1",
                     node_identifier= "Box1",publish_dcc_commands=False, mqtt_enhanced_debugging=False )

# Subscribe to the external feed fo DCC commands from node 2
set_signals_to_publish_state(10)
set_signals_to_publish_passed_events(3,11)
subscribe_to_signal_updates("Box2", main_callback_function,1)
subscribe_to_signal_passed_events("Box2", main_callback_function,1,12)
subscribe_to_dcc_command_feed("Box2")
                     
print ("Drawing Schematic and creating points")
canvas.create_line(0,100,750,100,fill="black",width=3) 
canvas.create_line(0,200,750,200,fill="black",width=3)

print ("Creating the track Occupancy Sections")
create_section (canvas,1,175,100,section_callback = main_callback_function)
create_section (canvas,2,425,100,section_callback = main_callback_function)
create_section (canvas,3,675,100,section_callback = main_callback_function)
create_section (canvas,12,75,200,section_callback = main_callback_function)
create_section (canvas,11,325,200,section_callback = main_callback_function)
create_section (canvas,10,575,200,section_callback = main_callback_function)

print ("Creating Signals")
create_colour_light_signal (canvas, 1, 50, 100,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback = main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False)
create_colour_light_signal (canvas, 2, 300, 100,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback = main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False)
create_colour_light_signal (canvas, 3, 550, 100,
                            signal_subtype = signal_sub_type.four_aspect,
                            sig_callback = main_callback_function,
                            sig_passed_button = True,
                            refresh_immediately = False)

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

print ("Entering Main Event Loop")
# Enter the main event loop and wait for a a callback event
window.mainloop()
