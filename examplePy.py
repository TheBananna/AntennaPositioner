from positionerComms import *

# We're going to utilize the features of this API
# THIS DOESN'T USE ALL OF THE METHODS, CHECK THE API FOR THE OTHERS


startup() # MUST be before any commands, this connects to the positoner over TCP and centers the positioners
#failure to do this will just crash the program


set_motion_parameters(10, 10, 10, 5) # Same as the default values but it seemed prudent to mention/show it
set_el_az(30, 45) # Moves the current positioner, az/el by default, to position 30° elevation 45° azimuth 
#the positioner will move at 5deg/s on the fastest axis and the other one adjust to finish at the same time
# set_elevation and set_azimuth are the same except they only change one axis

drive_el_az(-10, -15) # The same command as before, but this is a relative move, landing us at 20° elevation 30° azimuth once done


#it is also possible to wait until a move is finished as the movement methods return immediately if no other move is in progress
sleep(set_el_az(30, 45)) # All movement commands will return the time needed to execute the move


#Now onto the, admittedly dull, star of the show, the multi move system
#this will draw a 20° az/el circle in 300 steps
for i in range(301):
     add_move((-20 * sin(i / 300 * 2 * pi), -20 + 20 * cos(i / 300 * 2 * pi)))
program_moves() # clears the movement queue
run_moves() # executes the programmed moves, can be run infinite times after being programmed

# This will work to a lot of moves, 36,700 to be precise
# If you need more and can't afford to stop to program more in in the middle, you'll need to use velocity steering
# It's unideal in that it could use overshoot reduction improvements, but it will work with infinite moves
# It works by steering the positioner at a constant velocity in stepped directions, following a path
# A big downside is that it won't return until the overall movement is finished due to having to monitor and control the movement of the positioner

# So for the same circle:

for i in range(301):
     add_move((-20 * sin(i / 300 * 2 * pi), -20 + 20 * cos(i / 300 * 2 * pi)))
velocity_steer_run()


set_el_az(45, 45) # sends to 45 el 45 az
# If all you want is a circle, however, there is an easier method, circw (clockwise) and circcw (counterclockwise)
circw((45, 45), (0, 0))
# This will "draw" a circle starting from the current position, ending at the first parameter, and centered around the second
# Here that would be a circle of radius 63.6°
# circw and circcw technically draw circular arcs, however, hence the starting point at the end point for a circle
# Regardless, ensure your positioner is on the arc/circle you want to make before calling the method, undefined, though deterministic, behavior happens if that isn't done


# By default the API will use the az/el positioner, if you wish to change this call one of the methods that does so
switch_to_el_az() # Switches to el/az
switch_to_az_el() # And back again

# If there's issues with the program or for whatever reason you wish to restart the controller, call reboot()
reboot()
# It takes ~20 seconds to finish as it restarts the controller, waits 20 seconds, and then calls startup()

# In the even you wish to stop a currently executing move through code, call halt()
halt()
# It will immediately halt any of the set_* or drive_* moves
# It WILL NOT stop a movement sequence being executed, velocity steered or controller programmed

# And if one wishes to get the current elevation or azimuth
az = get_azimuth()
el = get_elevation()

