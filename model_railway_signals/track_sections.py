# --------------------------------------------------------------------------------
# This module is used for creating and managing Track Occupancy objects (sections)
#
# section_callback_type (tells the calling program what has triggered the callback):
#     section_callback_type.section_switched - The section has been toggled (occupied/clear) by the user
# 
# create_section - Creates a Track Occupancy section object
#   Mandatory Parameters:
#       Canvas - The Tkinter Drawing canvas on which the section is to be displayed
#       section_id:int - The ID to be used for the section 
#       x:int, y:int - Position of the section on the canvas (in pixels)
#       section_callback - The function to call if the section is manually toggled - default: null
#                         Note that the callback function returns (item_id, callback type)
#       label - The label to display on the section when occupied - default: "Train On Line"
# 
# section_occupied (section_id)- Returns the current state of the section (True=Occupied, False=Clear)
# 
# set_section_occupied (section_id) - Sets the specified section to "occupied"
#   Mandatory Parameters:
#       section_id:int - The ID to be used for the section 
#   Optional Parameters:
#       label - The label to display on the section when occupied - default: No Change
# 
# clear_section_occupied (section_id) - Sets the specified section to "clear"
#                   returns the current value of the Section Lable (as a string)
#
# --------------------------------------------------------------------------------

from . import common
from tkinter import *
import enum
import logging

# -------------------------------------------------------------------------
# Classes used by external functions when calling the create_point function
# -------------------------------------------------------------------------
    
# Define the different callbacks types for the section
class section_callback_type(enum.Enum):
    section_switched = 21   # The section has been manually switched by the user
    
# -------------------------------------------------------------------------
# sections are to be added to a global dictionary when created
# -------------------------------------------------------------------------

sections: dict = {}

# -------------------------------------------------------------------------
# Global references to the Entry box and the window we create it in
# -------------------------------------------------------------------------

text_entry_box = None
entry_box_window = None

# -------------------------------------------------------------------------
# The default "External" callback for the section buttons
# Used if this is not specified when the section is created
# -------------------------------------------------------------------------

def null_callback(section_id:int, callback_type):
    return(section_id, callback_type)

# -------------------------------------------------------------------------
# Internal Function to check if a section exists in the list of section
# Used in Most externally-called functions to validate the section ID
# -------------------------------------------------------------------------

def section_exists(section_id:int):
    return (str(section_id) in sections.keys() )

# -------------------------------------------------------------------------
# Callback for processing Button presses (manual toggling of Track Sections
# -------------------------------------------------------------------------

def section_button_event (section_id:int):
    global logging
    logging.info ("Section "+str(section_id)+": Track Section Toggled *****************************")
    toggle_section(section_id)
    sections[str(section_id)]["extcallback"] (section_id,section_callback_type.section_switched)
    return ()

# -------------------------------------------------------------------------
# Internal function to flip the state of the section. This Will SET/UNSET
# the section and initiate an external callback if one is specified
# -------------------------------------------------------------------------

def toggle_section (section_id:int):
    global sections
    global logging
    if sections[str(section_id)]["occupied"]:
        # section is on
        logging.info ("Section "+str(section_id)+": Changing to CLEAR")
        sections[str(section_id)]["occupied"] = False
        sections[str(section_id)]["button1"].config(relief="raised", bg="grey", fg="grey40",
                                            activebackground="grey", activeforeground="grey40")
    else:
        # section is off
        logging.info ("Section "+str(section_id)+": Changing to OCCUPIED")
        sections[str(section_id)]["occupied"] = True
        sections[str(section_id)]["button1"].config(relief="sunken", bg="black",fg="white",
                                            activebackground="black", activeforeground="white")
    return()

# -------------------------------------------------------------------------
# Internal function to get the new label text from the entry widget (on RETURN)
# -------------------------------------------------------------------------

def update_identifier(section_id):
    global sections 
    global text_entry_box
    global entry_box_window
    # Set the new label for the section button and set the width to the width it was created with
    # If we get back an empty string then set the label back to the default (OCCUPIED)
    new_section_label =text_entry_box.get()
    if new_section_label=="": new_section_label="OCCUPIED"
    sections[str(section_id)]["button1"]["text"] = new_section_label
    sections[str(section_id)]["button1"].config(width=sections[str(section_id)]["labellength"])
    # Assume that by entering a value the user wants to set the section to OCCUPIED
    if not sections[str(section_id)]["occupied"]: toggle_section(section_id)
    # Make an external callback to indicate something has changed
    sections[str(section_id)]["extcallback"] (section_id,section_callback_type.section_switched)
    # Clean up by destroying the entry box and the window we created it in
    text_entry_box.destroy()
    sections[str(section_id)]["canvas"].delete(entry_box_window)
    return()

# -------------------------------------------------------------------------
# Internal function to close the entry widget (on ESCAPE)
# -------------------------------------------------------------------------

def cancel_update(section_id):
    global text_entry_box
    global entry_box_window
    # Clean up by destroying the entry box and the window we created it in
    text_entry_box.destroy()
    sections[str(section_id)]["canvas"].delete(entry_box_window)
    return()

# -------------------------------------------------------------------------
# Internal function to create an entry widget (when button right clicked)
# -------------------------------------------------------------------------

def open_entry_box(section_id):
    global text_entry_box
    global entry_box_window
    canvas = sections[str(section_id)]["canvas"]
    # If another text entry box is already open then close that first
    if entry_box_window is not None:
        text_entry_box.destroy()
        canvas.delete(entry_box_window)
    # Set the font size and length for the text entry box
    font_size = common.fontsize
    label_length = sections[str(section_id)]["labellength"]
    # Create the entry box and bind the RETURN and ESCAPE events to it
    text_entry_box = Entry(canvas,width=label_length,font=('Ariel',font_size,"normal"))
    text_entry_box.bind('<Return>', lambda event:update_identifier(section_id))
    text_entry_box.bind('<Escape>', lambda event:cancel_update(section_id))
    # if the section button is already showing occupied then we EDIT the value
    if sections[str(section_id)]["occupied"]:
        text_entry_box.insert(0,sections[str(section_id)]["button1"]["text"])
    # Create a window on the canvas for the Entry box (overlaying the section button)
    x =  sections[str(section_id)]["positionx"]
    y =  sections[str(section_id)]["positiony"]
    entry_box_window = canvas.create_window (x,y,window=text_entry_box)
    # Force focus on the entry box so it will accept the keyboard entry immediately
    text_entry_box.focus()
    return()

# -------------------------------------------------------------------------
# Externally called function to create a section (drawing objects + state)
# All attributes (that need to be tracked) are stored as a dictionary
# This is then added to a dictionary of sections for later reference
# -------------------------------------------------------------------------

def create_section (canvas, section_id:int, x:int, y:int,
                    section_callback = null_callback,
                    label:str = "OCCUPIED"):
    global sections
    global logging
    logging.info ("Section "+str(section_id)+": Creating Track Occupancy Section")
    # Find and store the root window (when the first signal is created)
    if common.root_window is None: common.find_root_window(canvas)
    # Verify that a section with the same ID does not already exist
    if section_exists(section_id):
        logging.error ("Section "+str(section_id)+": Section already exists")
    elif section_id < 1:
        logging.error ("Section "+str(section_id)+": Section ID must be greater than zero")
    else:
        # Create the button objects and their callbacks
        font_size = common.fontsize
        section_button = Button (canvas, text=label, state="normal", relief="raised",
                    padx=common.xpadding, pady=common.ypadding, font=('Ariel',font_size,"normal"),
                    bg="grey", fg="grey40", activebackground="grey", activeforeground="grey40",
                    command = lambda:section_button_event(section_id))
        canvas.create_window (x,y,window=section_button) 
        # Compile a dictionary of everything we need to track
        sections[str(section_id)] = {"canvas" : canvas,                   # canvas object
                                     "button1" : section_button,          # drawing object
                                     "extcallback" : section_callback,    # External callback to make
                                     "labellength" : len(label),          # The fixed length for the button
                                     "positionx" : x,                     # Position of the button on the canvas
                                     "positiony" : y,                     # Position of the button on the canvas
                                     "occupied" : False }                 # Current state
        # Fix the width of the button (if text is edited late this won't change)
        section_button.config(width = sections[str(section_id)]["labellength"])
        # Bind the Middle and Right Mouse clicks to the section button - to open the entry box
        section_button.bind('<Button-2>', lambda event:open_entry_box(section_id))
        section_button.bind('<Button-3>', lambda event:open_entry_box(section_id))
    return()

# -------------------------------------------------------------------------
# Externally called function to Return the current state of the section
# -------------------------------------------------------------------------

def section_occupied (section_id:int):
    global logging
    # Validate the section exists
    if not section_exists(section_id):
        logging.error ("Section "+str(section_id)+": section_occupied - Section does not exist")
        occupied = False
    else:   
        occupied = sections[str(section_id)]["occupied"]
    return(occupied)

# -------------------------------------------------------------------------
# Externally called functions to Set and Clear a section
# -------------------------------------------------------------------------

def set_section_occupied (section_id:int,label:str=None):
    global logging
    # Validate the section exists
    if not section_exists(section_id):
        logging.error ("Section "+str(section_id)+": set_section_occupied - Section does not exist")
    elif not section_occupied(section_id):
        toggle_section(section_id)
        if label is not None: sections[str(section_id)]["button1"]["text"] = label
    return()

def clear_section_occupied (section_id:int):
    global logging
    # Validate the section exists
    if not section_exists(section_id):
        logging.error ("Section "+str(section_id)+": clear_section_occupied - Section does not exist")
    elif section_occupied(section_id):
        toggle_section(section_id)
    return(sections[str(section_id)]["button1"]["text"])

###############################################################################

