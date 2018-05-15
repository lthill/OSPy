TODO List for OSPy
====
(using pihrt fork for now)

# Features
## Add text describing "usage" under Stations settings.

### Add field for notes on the respective pages/stations.
Would like an area where one can record notes about setup, adjustments, or other information which 
you might want to reference in the future. Setup notes, station soil and vegetations types, 
exposure, things to check next time you are in the system, et cetera.

### Graphical map of zones
Graphical map of zones, eye candy

### Station Types
See if station type can use RF as done with Opensprinkler-pi and Brian Koblenz's SIP fork
https://github.com/bkoblenz/HVAC/blob/master/sip.py
This may require moving to pigpio for faster IO 

### Flow meter
Tally flow
Leak inspect as done with Opensprinkler-pi and Brian Koblenz's SIP fork 
https://github.com/bkoblenz/HVAC/blob/master/sip.py

### Compressor blowout plugin for winterization
Create plugin which can be used to automatically run a blowout routine
One should not have to waste an afternoon winterizing your sprinkler system when your sprinkler 
controller can do it for you! Connect the compressor, select the program, and go do something else.

Typical consumer grade compressors have tanks which are too small, have low flow, and are not 
designed for high duty cycles necessary for sprinkler blowout work. Using the controller to 
automatically run the blowout process and by deploying some additional tricks to overcome the 
limitations of consumer compressors.

* For system blowout run time is not so important as the number of cycles required to remove the 
water.
* The number of cycles needed will depend on the zone and the compressor used.
* At minimum each cycle will have a timed interval where the valve is open and a delay to allow for 
pressure recovery and cooling time for the compressor.
* The number of cycles per station, station open time, and cycle delay (rest time) will have to be 
set empirically by the user.


An enhanced system could use pressure signaling to close the station valve when the pressure drops 
below some threshold. The station valve may be opened again when the presure recovers and/or the 
delay timer has expired.

The addition of a pressure regulator between the compressor and blowout port would add to the tank 
volume, first between the tank and regulator, then beteween the blowout port and the station valve. 
With this larger volume pressure recovery will take longer and one may need to impose a maximum 
duty cycle limitation on the compressor via a run relay.

TODO - Work out logic and see if a conventional compressor pressure pressure control switch would 
be suitable for signalling and/or run relay.


# Tasks
### Find watering months used by water company.
Sewage rates are set by consumption in non-watering months.

### Diagnose "no location error" in weather based watering level plugin weather.py.
1. Could not find location with zip code
2. Could not find location with city
3. Found location with geographic coordinates
4. Works with City,State abbreviation
5. Tried city again works.
6. Reverted to geographic coordinates
Cause unresolved
