import badger2040
import qrcode
import time
import os
#from machine import Pin, ADC
import machine
# Global Constants
# for e.g. 2xAAA batteries, try max 3.4 min 3.0
MAX_BATTERY_VOLTAGE = 3.1
MIN_BATTERY_VOLTAGE = 2.0

WIDTH = badger2040.WIDTH
HEIGHT = badger2040.HEIGHT

BATT_WIDTH = 200
BATT_HEIGHT = 100
BATT_BORDER = 10
BATT_TERM_WIDTH = 20
BATT_TERM_HEIGHT = 50
BATT_BAR_PADDING = 10
BATT_BAR_HEIGHT = BATT_HEIGHT - (BATT_BORDER * 2) - (BATT_BAR_PADDING * 2)
BATT_BAR_START = ((WIDTH - BATT_WIDTH) // 2) + BATT_BORDER + BATT_BAR_PADDING
BATT_BAR_END = ((WIDTH + BATT_WIDTH) // 2) - BATT_BORDER - BATT_BAR_PADDING

NUM_BATT_BARS = 4


display = badger2040.Badger2040()

code = qrcode.QRCode()


# ------------------------------
#      Utility functions
# ------------------------------


def map_value(input, in_min, in_max, out_min, out_max):
    return (((input - in_min) * (out_max - out_min)) / (in_max - in_min)) + out_min


# ------------------------------
#      Drawing functions
# ------------------------------

def draw_battery_icon(level, x, y):
    # Outline
    # print("Level = ", level)
    display.thickness(1)
    display.pen(15)
    display.rectangle(x, y, 19, 10)
    # Terminal
    display.rectangle(x + 19, y + 3, 2, 4)
    display.pen(0)
    display.rectangle(x + 1, y + 1, 17, 8)
    if level < 1:
        display.pen(0)
        display.line(x + 3, y, x + 3 + 10, y + 10)
        display.line(x + 3 + 1, y, x + 3 + 11, y + 10)
        display.pen(15)
        display.line(x + 2 + 2, y - 1, x + 4 + 12, y + 11)
        display.line(x + 2 + 3, y - 1, x + 4 + 13, y + 11)
        return
    # Battery Bars
    display.pen(15)
    for i in range(4):
        if level / 4 > (1.0 * i) / 4:
            display.rectangle(i * 4 + x + 2, y + 2, 3, 6)

state = {
    "current_scrn": 0
}


def measure_qr_code(size, code):
    w, h = code.get_size()
    module_size = int(size / w)
    return module_size * w, module_size


def draw_qr_code(ox, oy, size, code):
    size, module_size = measure_qr_code(size, code)
    display.pen(15)
    display.rectangle(ox, oy, size, size)
    display.pen(0)
    for x in range(size):
        for y in range(size):
            if code.get_module(x, y):
                display.rectangle(ox + x * module_size, oy + y * module_size, module_size, module_size)


def draw_qr_card1():
    display.led(128)
    #code_text = "https://inspiresemi.com"
    code_text2 = "BEGIN:VCARD\nVERSION:4.\nN:Karasek;Marc\nEMAIL:mkarasek@inspiresemi.com\nTEL:678-770-3788\nEND:VCARD"
    name = "Marc Karasek"
    job_descript = "Dir Software Engineering"
    company = "InspireSemi Inc."
    email = "mkarasek@inspiresemi.com"

    # Clear the Display
    display.pen(15)  # Change this to 0 if a white background is used
    display.clear()
    display.pen(0)

    code.set_text(code_text2)
    size, _ = measure_qr_code(96, code)
    left = 5
    top = int((badger2040.HEIGHT / 2) - (size / 2))
    print("size ", size, "top ", top, "height ", badger2040.HEIGHT)
    draw_qr_code(left, top-10, 96, code)

    left = 90 + 5
    display.thickness(2)
    display.font("serif")
    display.text(name, left, 20, .75)
    display.thickness(2)
    
    top = 60
    display.font("sans")
    display.text(job_descript, left, 60, 0.5)
    display.text(company, left, 80, 0.5)
    display.font("sans")
    display.text(email, left - 75, 110, 0.6)


def draw_qr_card2():
    display.led(128)
    code_text = "https://inspiresemi.com"
    name = "InspireSemi Inc."

    # Clear the Display
    display.pen(15)  # Change this to 0 if a white background is used
    display.clear()
    display.pen(0)

    code.set_text(code_text)
    size, _ = measure_qr_code(128, code)
    left = 5
    top = int((badger2040.HEIGHT / 2) - (size / 2))
    print("size ", size, "top ", top, "height ", badger2040.HEIGHT)
    draw_qr_code(left, top, 128, code)

    left =128 + 5
    display.thickness(2)
    display.font("sans")
    display.text(name, left, 20, .5)
    display.thickness(2)

# ------------------------------
#        Program setup
# ------------------------------

display.update_speed(badger2040.UPDATE_MEDIUM)

# Set up the ADCs for measuring battery voltage
vbat_adc = machine.ADC(badger2040.PIN_BATTERY)
vref_adc = machine.ADC(badger2040.PIN_1V2_REF)
vref_en = machine.Pin(badger2040.PIN_VREF_POWER)
vref_en.init(machine.Pin.OUT)
vref_en.value(0)

last_level = -1

def check_button():
    if display.pressed(badger2040.BUTTON_UP):
        if state["current_scrn"] == 0:
            state["current_scrn"] = 1
            qr2()
            return
        if state["current_scrn"] == 1:
            state["current_scrn"] = 0
            qr1()
            return

    if display.pressed(badger2040.BUTTON_DOWN):
        if state["current_scrn"] == 1:
            state["current_scrn"] = 0
            qr1()
            return
        if state["current_scrn"] == 0:
            state["current_scrn"] = 1
            qr2()
            return
        

def get_battery_level():
    # Battery measurement

    # Enable the onboard voltage reference
    vref_en.value(1)

    # Calculate the logic supply voltage, as will be lower that the usual 3.3V when running off low batteries
    vdd = 1.24 * (65535 / vref_adc.read_u16())
    vbat = (
        (vbat_adc.read_u16() / 65535) * 3 * vdd
    )  # 3 in this is a gain, not rounding of 3.3V

    # Disable the onboard voltage reference
    vref_en.value(0)
    #print("vbat = ", vbat)
    # Convert the voltage to a level to display onscreen
    return vbat

def wait_for_user_to_release_buttons():
    pr = display.pressed
    while pr(badger2040.BUTTON_UP) or pr(badger2040.BUTTON_DOWN):
        time.sleep(0.01)

def qr1():
    wait_for_user_to_release_buttons()
    # Draw the VCARD Business Card
    draw_qr_card1()
    # Get Battery Voltage
    vbat = get_battery_level()
    # Map it to 0-4
    bat = int(map_value(vbat, MIN_BATTERY_VOLTAGE, MAX_BATTERY_VOLTAGE, 0, 4))
    # print("Bat = ", bat)
    # Draw Icon in top right corner
    draw_battery_icon(bat, WIDTH - 22 - 3, 3)
    # update display
    display.update()
    # Halt the Badger to save power, it will wake up if any of the front buttons are pressed
    display.halt()
    #print("Out of halt1")
    #print("Screen", state["current_scrn"] )
    return
    
def qr2():
    wait_for_user_to_release_buttons()
    # Draw Company QR Code Page
    draw_qr_card2()
    # Get Batt Voltage
    vbat = get_battery_level()
    # Map to 0-4
    bat = int(map_value(vbat, MIN_BATTERY_VOLTAGE, MAX_BATTERY_VOLTAGE, 0, 4))
    # Draw Battery top right
    draw_battery_icon(bat, WIDTH - 22 - 3, 3)
    # Update screen
    display.update()
    # Halt the Badger to save power, it will wake up if any of the front buttons are pressed
    display.halt()
    #print("Out of halt2")
    #print("Screen", state["current_scrn"] )
    return

# ------------------------------
#       Main program loop
# ------------------------------

while True:
    check_button()

    #print("Screen", state["current_scrn"] )
        