from positionerComms import *

#We're going to utilize the features of this API

startup() # MUST be before any commands, this connects to the positoner over TCP and centers the positioners

set_motion_parameters(10, 10, 10, 5) # Same as the default values
set_el_az(30, 45) # Moves the current positioner, az/el by default, to position 30° elevation 45° azimuth 
#the positioner will move at 5deg/s on the fastest axis and the other one adjust to finish at the same time

drive_el_az(-10, -15) # The same command as before, but this is a relative move, landing us at 20° elevation 30° azimuth once done


#it is also possible to wait until a move is finished as the movement methods return immediately if no other move is in progress
sleep(set_el_az(30, 45)) # All movement commands will return the time needed to execute the move




