#!/usr/bin/env python
# This plugin sends data to I2C for LCD 16x2 or 16x1 char with PCF8574.
# Visit for more: www.pihrt.com/elektronika/258-moje-rapsberry-pi-i2c-lcd-16x2.
# This plugin requires python pylcd2.py library


import json
import time
import sys
import traceback
from datetime import datetime

from threading import Thread
from random import randint

import web
import helpers
import version
from inputs import inputs
from options import options
from log import log
from plugins import PluginOptions, plugin_url
from webpages import ProtectedPage


NAME = 'LCD Display'
LINK = 'settings_page'

lcd_options = PluginOptions(
    NAME,
    {
        "use_lcd": "off",
        "line": "off",
        "address": "0x20"
    }
)


################################################################################
# Main function loop:                                                          #
################################################################################
class LCDSender(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.status = ''

        self._sleep_time = 0
        self.start()

    def add_status(self, msg):
        if self.status:
            self.status += '\n' + msg
        else:
            self.status = msg
        print msg

    def update(self):
        self._sleep_time = 0

    def _sleep(self, secs):
        self._sleep_time = secs
        while self._sleep_time > 0:
            time.sleep(1)
            self._sleep_time -= 1

    def run(self):
        time.sleep(randint(3, 10))  # Sleep some time to prevent printing before startup information
        log.debug(NAME, "LCD plugin is active")
        text_shift = test_text_shift()

        while True:
            try:
                if lcd_options['use_lcd'] != 'off':  # if LCD plugin is enabled
                    if lcd_options['line'] == 'on':  # if line is 2 (16x2 LCD)
                        if text_shift > 9:  # Print 0-9 messages to LCD 16x2
                            text_shift = 0
                            self.status = ''
                    elif lcd_options['line'] == 'off':  # line is 1 (16x1 LCD)
                        if text_shift > 119:  # Print 100-119 messages to LCD 16x1
                            text_shift = 100
                            self.status = ''

                    if (text_shift > 10) and (text_shift < 100):
                        text_shift = 0

                    get_LCD_print(self, text_shift)  # Print to LCD 16x2 or 16x1
                    text_shift += 1  # Increment text_shift value

                self._sleep(4)

            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_string = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
                self.add_status('LCD plugin encountered error: ' + err_string)
                self._sleep(60)


lcd_sender = None


################################################################################
# Helper functions:                                                            #
################################################################################
def start():
    global lcd_sender
    if lcd_sender is None:
        lcd_sender = LCDSender()


def stop():
    global lcd_sender
    if lcd_sender is not None:
        lcd_sender.stop()
        lcd_sender.join()
        lcd_sender = None


def get_LCD_print(self, report):
    """Print messages to LCD 16x2"""

    find_i2c = 'True'
    lcd_adr = 0
    pcf_type = 'None'

    import pylcd2  # Library for LCD 16x2 PCF8574
    import smbus

    bus = smbus.SMBus(1 if helpers.get_rpi_revision() >= 2 else 0)

    # find i2c adress
    for addr in range(32, 39):  # PCF8574 range 0x20-0x27
        if find_i2c == 'True':
            try:
                bus.write_quick(addr)
                lcd_adr = addr
                find_i2c = 'False'
                pcf_type = 'PCF8574'
                self.add_status('Find: ' + pcf_type + ' on adress 0x' + ('%02x' % lcd_adr))

            except:
                find_i2c = 'True'

    for addr in range(56, 63):  # PCF8574A range 0x38-0x3F
        if find_i2c == 'True':
            try:
                bus.write_quick(addr)
                lcd_adr = addr
                find_i2c = 'False'
                pcf_type = 'PCF8574A'
                self.add_status('Find: ' + pcf_type + ' on adress 0x' + ('%02x' % lcd_adr))

            except:
                find_i2c = 'True'

    if find_i2c == 'False':
        # Address for PCF8574 = example 0x20, Bus Raspi = 1 (0 = 256MB, 1=512MB)
        lcd = pylcd2.lcd(lcd_adr, 1 if helpers.get_rpi_revision() >= 2 else 0)
        if report == 0:
            lcd.lcd_clear()
            lcd.lcd_puts("Open Sprinkler", 1)
            lcd.lcd_puts("Irrigation syst.", 2)
            self.add_status('Open Sprinkler / Irrigation syst.')
        elif report == 1:
            lcd.lcd_clear()
            lcd.lcd_puts("Software OSPy:", 1)
            lcd.lcd_puts(version.ver_str, 2)
            self.add_status('Software OSPy: / ' + version.ver_date)
        elif report == 2:
            lcd.lcd_clear()
            ip = helpers.get_ip()
            lcd.lcd_puts("My IP is:", 1)
            lcd.lcd_puts(str(ip), 2)
            self.add_status('My IP is: / ' + str(ip))
        elif report == 3:
            lcd.lcd_clear()
            lcd.lcd_puts("Port IP:", 1)
            lcd.lcd_puts("8080", 2)
            self.add_status('Port IP: / 8080')
        elif report == 4:
            lcd.lcd_clear()
            temp = helpers.get_cpu_temp(options.temp_unit) + ' ' + options.temp_unit
            lcd.lcd_puts("CPU temperature:", 1)
            lcd.lcd_puts(temp, 2)
            self.add_status('CPU temperature: / ' + temp)
        elif report == 5:
            lcd.lcd_clear()
            now = datetime.now()
            da = now.strftime('%d.%m.%Y')
            ti = now.strftime('%H:%M:%S')
            lcd.lcd_puts(da, 1)
            lcd.lcd_puts(ti, 2)
            self.add_status(da + ' ' + ti)
        elif report == 6:
            lcd.lcd_clear()
            up = helpers.uptime()
            lcd.lcd_puts("System run time:", 1)
            lcd.lcd_puts(up, 2)
            self.add_status('System run time: / ' + up)
        elif report == 7:
            lcd.lcd_clear()
            if inputs.rain_sensed():
                rain_sensor = "Active"
            else:
                rain_sensor = "Inactive"
            lcd.lcd_puts("Rain sensor:", 1)
            lcd.lcd_puts(rain_sensor, 2)
            self.add_status('Rain sensor: / ' + rain_sensor)
        elif report == 8:
            lcd.lcd_clear()
            try:
                from pressure_adj import get_check_pressure

                state_press = get_check_pressure()
                if state_press:
                    lcd.lcd_puts("Pressure sensor:", 1)
                    lcd.lcd_puts("GPIO is HIGH", 2)
                    self.add_status('Pressure sensor: / GPIO is HIGH')

                else:
                    lcd.lcd_puts("Pressure sensor:", 1)
                    lcd.lcd_puts("GPIO is LOW", 2)
                    self.add_status('Pressure sensor: / GPIO is LOW')

            except:
                lcd.lcd_puts("Pressure sensor:", 1)
                lcd.lcd_puts("Not used", 2)
                self.add_status('Pressure sensor: / Not used')
        elif report == 9:
            lcd.lcd_clear()
            if gv.lrun[1] == 98:
                pgr = 'Run-once'
            elif gv.lrun[1] == 99:
                pgr = 'Manual'
            else:
                pgr = str(gv.lrun[1])
            stop = time.gmtime(gv.lrun[2])
            if pgr != '0':
                logline2 = 'P' + pgr + ' ' + timestr(gv.lrun[2])
            else:
                logline2 = 'None'
            lcd.lcd_puts('Last program', 1)
            lcd.lcd_puts(logline2, 2)
            self.add_status('Last program / ' + logline2)

        #------- end text to 16x2 -----------------

        elif report == 100:  # start text to 16x1
            lcd.lcd_clear()
            lcd.lcd_puts("Open Sprinkler", 1)
            self.add_status('Open Sprinkler')
        elif report == 101:
            lcd.lcd_clear()
            lcd.lcd_puts("Irrigation syst.", 1)
            self.add_status('Irrigation syst.')
        elif report == 102:
            lcd.lcd_clear()
            lcd.lcd_puts("Software OSPy:", 1)
            self.add_status('Software OSPy:')
        elif report == 103:
            lcd.lcd_clear()
            lcd.lcd_puts(version.ver_date, 1)
            self.add_status(version.ver_date)
        elif report == 104:
            lcd.lcd_clear()
            lcd.lcd_puts("My IP is:", 1)
            self.add_status('My IP is:')
        elif report == 105:
            lcd.lcd_clear()
            ip = helpers.get_ip()
            lcd.lcd_puts(str(ip), 1)
            self.add_status(str(ip))
        elif report == 106:
            lcd.lcd_clear()
            lcd.lcd_puts("Port IP:", 1)
            self.add_status('Port IP:')
        elif report == 107:
            lcd.lcd_clear()
            lcd.lcd_puts("8080", 1)
            self.add_status('8080')
        elif report == 108:
            lcd.lcd_clear()
            lcd.lcd_puts("CPU temperature:", 1)
            self.add_status('CPU temperature:')
        elif report == 109:
            lcd.lcd_clear()
            temp = helpers.get_cpu_temp(options.temp_unit) + ' ' + options.temp_unit
            lcd.lcd_puts(temp, 1)
            self.add_status(temp)
        elif report == 110:
            lcd.lcd_clear()
            da = datetime.now().strftime('%d.%m.%Y')
            lcd.lcd_puts("Date: " + da, 1)
            self.add_status('Date: ' + da)
        elif report == 111:
            lcd.lcd_clear()
            ti = datetime.now().strftime('%H:%M:%S')
            lcd.lcd_puts("Time: " + ti, 1)
            self.add_status('Time: ' + ti)
        elif report == 112:
            lcd.lcd_clear()
            lcd.lcd_puts("System run time:", 1)
            self.add_status('System run time:')
        elif report == 113:
            lcd.lcd_clear()
            up = helpers.uptime()
            lcd.lcd_puts(up, 1)
            self.add_status(up)
        elif report == 114:
            lcd.lcd_clear()
            lcd.lcd_puts("Rain sensor:", 1)
            self.add_status('Rain sensor:')
        elif report == 115:
            lcd.lcd_clear()
            if inputs.rain_sensed():
                rain_sensor = "Active"
            else:
                rain_sensor = "Inactive"
            lcd.lcd_puts(rain_sensor, 1)
            self.add_status(rain_sensor)
        elif report == 116:
            lcd.lcd_clear()
            lcd.lcd_puts('Last program', 1)
            self.add_status('Last program')
        elif report == 117:
            lcd.lcd_clear()
            if gv.lrun[1] == 98:
                pgr = 'Run-once'
            elif gv.lrun[1] == 99:
                pgr = 'Manual'
            else:
                pgr = str(gv.lrun[1])
            stop = time.gmtime(gv.lrun[2])
            if pgr != '0':
                logline2 = 'P' + pgr + ' ' + timestr(gv.lrun[2])
            else:
                logline2 = 'none'
            lcd.lcd_puts(logline2, 1)
            self.add_status(logline2)
        elif report == 118:
            lcd.lcd_clear()
            lcd.lcd_puts("Pressure sensor:", 1)
            self.add_status('Pressure sensor:')
        elif report == 119:
            lcd.lcd_clear()
            try:
                from pressure_adj import get_check_pressure

                state_press = get_check_pressure()
                if state_press:
                    lcd.lcd_puts("GPIO is HIGH", 1)
                    self.add_status('GPIO is HIGH')

                else:
                    lcd.lcd_puts("GPIO is LOW", 1)
                    self.add_status('GPIO is LOW')

            except:
                lcd.lcd_puts("Not used", 1)
                self.add_status('Not used')
    else:
        self.add_status('No find PCF8574 controller.')


def test_text_shift():
    datalcd = get_lcd_options()
    if datalcd['line'] != 'off':
        text_shift = 0  # 16x2 LCD
    else:
        text_shift = 100  # 16x1 LCD
    return text_shift


def get_lcd_options():
    """Returns the data form file."""
    datalcd = {
        'use_lcd': lcd_options['use_lcd'],
        'line': lcd_options['line'],
        'status': lcd_sender.status
    }

    return datalcd


################################################################################
# Web pages:                                                                   #
################################################################################
class settings_page(ProtectedPage):
    """Load an html page for entering lcd adjustments."""

    def GET(self):
        return self.template_render.plugins.lcd_display(get_lcd_options())

    def POST(self):
        lcd_options.web_update(web.input())

        lcd_sender.update()
        raise web.seeother(plugin_url(settings_page))


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format."""

    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        return json.dumps(get_lcd_options())
