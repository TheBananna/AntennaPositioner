#There are a few method in here that will interest a user of the antenna positioners
#
#Firstly one must call the startup method, this will connect to the ACR controller and initialize/zero everything
#After that there are several move methods, set_elevation, set_azimuth, set_el_az, and drive_el_az
#The first three simply move the antenna positioner to absolute degree cordinates, drive_el_az does a relative move
#It is worth noting that both set_el_az and drive_el_az will scale one of the movement axis to finish both at the same time
#and commands will only run after the previous one has, so set_elevation followed by set_azimuth will result in an elevation change and then an azimuth change
#bring_to_home is the same as set_el_az(0,0)
#get_azimuth and get_elevation return the current azimuth and elevation in degrees
#set_motion parameters sets the start, deceleration, and stop accelerations in degrees/sec^2, velocity is the sweep velocity in degrees/sec
#velocity cannot be higher than 5 deg/sec for motor safety reasons
#halt immediately stops all movement
#reboot restarts the controller and calls startup in case something has gone wrong and a good state needs to be restored
#switch_to_el_az and switch_to_az_el switch the current target of the movement commands to those motors, this doesn't effect startup
#add_moves and add_move are to add moves to the internal move queue used for programming continuous piecewise motion into the controller, the format of the moves is (x, y)
#program_moves programs _move_queue into the controller and then clears _move_queue, this overwrites previously programmed moves and is lost upong reboot or power loss
#run_moves executes previously programmed moves 


import socket
from time import sleep
from math import *
_ip_address = '192.168.100.1'  
_port = 5002
_motors = None
_centers = None
_ratios = None
_vel = 4.9


def _dumb_transmit(sock, command):
    sock.sendall(command.encode('ascii'))
    print(f'Sent: {command}')
    sleep(.1)#assumes the controller recieved it and has responded by now
    return sock.recv(1024).decode('ascii')

def _transmit(sock, command):
    sock.sendall(command.encode('ascii'))
    print(f'Sent: {command}'.replace('\r\n', ''))
    full_response = ''
    while True: # waits for a response from the controller before continuing
        sleep(.01)
        response = sock.recv(1024)
        response = response.decode('ascii')
        full_response += response
        if 'P00>' in full_response or 'SYS>' in full_response:
            break
    print('Received:', response)
    return response


def send_ascii_command(command):
   
    #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    command = command + '\r\n'
    try:
        #sock.connect((ip_address, port))
        count = 0
        while 'Unknown command' in (response := _transmit(_sock, command)) and count < 5:
            send_ascii_command('PROG0') 
            count+=1
        if count == 5:
            print('RETRY COMMUNICATION')
            return ''
        return response
    except Exception as e:
        print('Error:', str(e))
        #send_ascii_command(ip_address, port, command)
    finally:
        #sock.close()
        pass


def set_elevation(elev):
    if(abs(elev) > 90):
        raise Exception('Elevation cannot go above or below 90 degrees')
    command = f'{_motors[0]}{elev}'
    send_ascii_command(command)
    return abs(get_elevation() - elev) / _vel


def set_azimuth(azi):
    command = f'{_motors[1]}{azi}'
    send_ascii_command(command)
    return abs(get_azimuth() - azi) / _vel


def _decode_response(response):
    try:
        r = response.split()
        longest = ''
        for s in r:
            if(s.replace('-', '').replace('.', '').isdecimal() and len(s) > len(longest)):
                longest = s
        return float(longest)
    except Exception:
        return None


def _cold_start():
    d_el = (_centers[0] - get_elevation() / 360 * _ratios[0]) / _ratios[0] * 360
    if(d_el > 360):
        d_el = d_el % 360
    if(d_el < -360):
        d_el = -(-d_el %360)

    d_az = (_centers[1] - get_azimuth() / 360 * _ratios[1]) / _ratios[1] * 360
    if(d_az > 360):
        d_az = d_az % 360
    if(d_az < -360):
        d_az = -(-d_az %360)
    
    return drive_el_az(round(d_el, 5), round(d_az, 5), True)

def startup():
    global _sock
    switch_to_az_el()
    _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _sock.connect((_ip_address, _port))
    _dumb_transmit(_sock, 'PROG0\r\n')
    _dumb_transmit(_sock, 'DRIVE ON X Y Z A\r\n')
    set_motion_parameters(10, 10, 10, _vel)
    if(int(_decode_response(send_ascii_command('? started'))) == 1): #if already started, we just have to send the motors home
        #sleep(back_to_normal())
        wait = bring_to_home()
        switch_to_el_az()
        #sleep(back_to_normal())
        wait = max(wait, bring_to_home())
        switch_to_az_el()
        sleep(wait)
        return
    

    stall = _cold_start()
    #send_ascii_command('PROG0')

    switch_to_el_az()
    stall = max(stall, _cold_start())
    #send_ascii_command('PROG0')

    sleep(stall)
    switch_to_az_el()
    send_ascii_command('started=1')
    reset()
    #send_ascii_command('DIM MBUF (20)')
    #send_ascii_command('MBUF ON')


def reset():
    send_ascii_command('RES X RES Y RES Z RES A')


def bring_to_home():
    send_ascii_command(f'{_motors[0]}0 {_motors[1]}0')
    return max(abs(get_elevation()), abs(get_azimuth())) / _vel


_curr_azi = 0
def get_azimuth():
    azi = _decode_response(send_ascii_command(f'? {_pos_alias[1]}'))
    if azi is None:
        return get_azimuth()
    _curr_azi = azi
    return azi / _ratios[1] * 360


_curr_el = 0
def get_elevation():
    el = _decode_response(send_ascii_command(f'? {_pos_alias[0]}'))
    if el is None:
        return get_elevation()
    _curr_el = el
    return el / _ratios[0] * 360


def set_el_az(elev, azi):
    if(abs(elev) > 90):
        raise Exception('Elevation cannot go above or below 90 degrees')
    command = f'{_motors[0]}{elev} {_motors[1]}{azi}'
    send_ascii_command(command)
    return max(abs(get_elevation() - elev), abs(get_azimuth()) - azi) / _vel


def drive_el_az(el, az, ignore_limits=False):
    #print(f'el az are {(get_elevation(), get_azimuth())}')
    if(not ignore_limits and abs(get_elevation() + el) > 90):
        raise Exception('Elevation cannot go above or below 90 degrees')
    send_ascii_command(f'{_motors[0]}/{el} {_motors[1]}/{az}')
    return max(abs(el), abs(az)) / _vel


def set_motion_parameters(acc, dec, stp, vel):
    if(vel > 5):
        raise Exception('Velocity cannot be higher than 5 deg/s')
    _vel = vel
    send_ascii_command(f'ACC {acc} DEC {dec} STP {stp} VEL {_vel}')

def get_motion_parameters():
    ac = float(_decode_response(send_ascii_command('? ACC')))
    de = float(_decode_response(send_ascii_command('? DEC')))
    st = float(_decode_response(send_ascii_command('? STP')))
    ve = float(_decode_response(send_ascii_command('? VEL')))
    return ac, de, st, ve
    

def halt():
    send_ascii_command('HALT ALL')


def reboot():
    global sock
    _dumb_transmit(_sock, 'reboot')
    _sock.close()
    sleep(20) # found to work well but may need to be increased for reliability
    startup()

def switch_to_az_el():
    global _motors, _centers, _ratios, _pos_alias
    _motors = ['X', 'Y']
    _centers = [3029374, 34538205]  # experimentally determined
    _ratios = [189 * 2**19, 765 * 2**19]            
    _pos_alias = ['P12290', 'P12546']

def switch_to_el_az():
    global _motors, _centers, _ratios, _pos_alias
    _motors = ['A', 'Z']
    _centers = [27432018, 3121654]   # experimentally determined
    _ratios = [153*2**19, 153*2**19]            
    _pos_alias = ['P13058', 'P12802']


#Circle clockwise. Moves around the center from the current position to the target in a circular arc
def circw(target, center):
    v1, v2 = (get_elevation() - center[0], get_azimuth() - center[1]), (target[0] - center[0], target[1] - center[1])   #gets the vectors pointing from the starting and target positions to the center
    t1, t2 = atan2(v1[1], v1[0]) / 2 / pi * 360, atan2(v2[1], v2[0]) / 2 / pi * 360                                     #gets the angles of those vectors
    circumference = sqrt(v2[0]**2 + v2[1]**2) * pi * 2                                                                  #calculates the circumference of the full circle in degrees
    send_ascii_command(f'CIRCW {_motors[0]} ({target[0]},{center[0]}) {_motors[1]} ({target[1]},{center[1]})')          
    return circumference * ((t1 - t2) % 360) / 360 / _vel                                                               #returns the time to traverse the relavant arc of the circle



#Circle counter clockwise. Moves around the center from the current position to the target in a circular arc
def circcw(target, center):
    v1, v2 = (get_elevation() - center[0], get_azimuth() - center[1]), (target[0] - center[0], target[1] - center[1])
    t1, t2 = atan2(v1[1], v1[0]) / 2 / pi * 360, atan2(v2[1], v2[0]) / 2 / pi * 360
    circumference = sqrt(v2[0]**2 + v2[1]**2) * pi * 2 
    send_ascii_command(f'CIRCCW {_motors[0]} ({target[0]},{center[0]}) {_motors[1]} ({target[1]},{center[1]})')
    return circumference * (360 - (t1 - t2) % 360) / 360 / _vel


#turns on TARC, turning normal moves into spline interpolated ones
#with this on the current position is the starting point, the next move is the intermediate point, and the last move is the end point
#after the last move is given the motor will start moving
#this prevents queued moves from working
#TARC usage would look like the following
# tarc_on()
# set_el_az(45, 23)     Intermediate move, nothing happens yet
# set_el_az(93, 75)     Final position is aquired and movement begins
def tarc_on():
    send_ascii_command('TARC ON X Y Z A')


#Turns off TARC and renables normal movement
def tarc_off():
    send_ascii_command('TARC OFF X Y Z A')


#JOG SYSTEM
import datetime
import ctypes

_move_queue = []
_pos_alias = []
#needs to be a list of tuples each formatted as (x, y, vel_x, vel_y, accel, decel) or (x, y)
def add_moves(moves):
    global _move_queue
    _move_queue += moves

def add_move(move):
    global _move_queue
    _move_queue.append(move)

def program_moves():#Should start on the starting position
    global _move_queue
    accel, decel, stp, vel = get_motion_parameters()
    last_el = get_elevation()
    last_az = get_azimuth()
    send_ascii_command('NEW')
    #send_ascii_command('DIM MBUF(20)')
    #send_ascii_command('MBUF ON')
    send_ascii_command('PROGRAM')    
    try:
        send_ascii_command(f'ACC {accel} DEC {decel} STP 0 VEL {vel}') # a stop acceleration of 0 means the move doesn't stop at the end if there's another move in the buffer 
        #send_ascii_command('LOOK ON')
        #send_ascii_command('LOOK MODE 1')

        for i, move in enumerate(_move_queue):
            send_ascii_command(f'{_motors[0]}{round(move[0], 4)} {_motors[1]}{round(move[1], 4)}')
    except Exception as e:
        send_ascii_command('ENDP')
        raise e
    _move_queue = []
    send_ascii_command(f'ACC {accel} DEC {decel} STP {stp} VEL {vel}')
    #_dumb_transmit('LOOK OFF')
    send_ascii_command('ENDP') 


def run_moves():
    _dumb_transmit(_sock, 'run prog0')

# def run_moves():
#     global _move_queue
#     accel, decel, stp, vel = get_motion_parameters()
#     def sign(n):
#         if(n == 0):
#             return 0
#         return n / abs(n)
#     set_el_az(_move_queue[0][0], _move_queue[0][1])\
    
#     send_ascii_command(f'jog acc x{accel} y{accel} z{accel} a{accel}')
#     send_ascii_command(f'jog dec x{decel} y{decel} z{decel} a{decel}')
#     send_ascii_command(f'jog vel x{vel} y{vel} z{vel} a{vel}')

#     for i, move in enumerate(_move_queue[1:len(_move_queue) - 1]): #_move_queue must start with the starting position
#         i = i + 1
#         vec = (move[0] - _move_queue[i-1][0], move[1] - _move_queue[i-1][1])
#         #vec = (move[0] - get_elevation(), move[1] - get_azimuth()) # for whatever reason this doesn't work at all but the previous works ok
#         mag = sqrt(vec[0]**2 + vec[1]**2)
#         vec = (vec[0] / mag*vel, vec[1] / mag*vel)
#         send_ascii_command(f'jog vel {_motors[0]}{abs(round(vec[0], 4))} {_motors[1]}{abs(round(vec[1], 4))}')
#         #send_ascii_command(f'jog abs {_motors[0]}{move[0]} {_motors[1]}{move[1]}')
#         send_ascii_command(f'jog {"fwd" if vec[0] > 0 else "rev"} {_motors[0]}')
#         send_ascii_command(f'jog {"fwd" if vec[1] > 0 else "rev"} {_motors[1]}')
        
#         next_vec = (_move_queue[i+1][0] - move[0], _move_queue[i+1][1] - move[1])
#         mag = sqrt(next_vec[0]**2 + next_vec[1]**2)
#         next_vec = (next_vec[0] / mag * vel, next_vec[1] / mag * vel)
#         #d_vec = (next_vec[0]**2 - vec[0]**2, next_vec[1]**2 - vec[1]**2)
#         d_vec = (next_vec[0] - vec[0], next_vec[1] - vec[1])
#         criterion = max(abs(d_vec[0]), abs(d_vec[1])) > .1
#         if (abs(vec[0]) > abs(vec[1])):#wanted to use d_vec only but that was running into a vanishing gradient type situation when both were small 
#             while ((el := get_elevation()) > move[0] - d_vec[0]/2/accel) if vec[0] < 0 else (el := get_elevation()) < move[0] - d_vec[0]/2/accel:
#                 pass
#                 #print(f'Waiting until {round(move[0] - d_vec[0]/accel, 2)}el at {el} at {datetime.datetime.now().second} secs at {i}')
#         else:
#             while ((az := get_azimuth()) > move[1] - d_vec[1]/2/accel) if vec[1] < 0 else (az := get_azimuth()) < move[1] - d_vec[1]/2/accel:
#                 pass
#                 #print(f'Waiting until {round(move[1] - d_vec[1]/accel, 2)}az at {az} at {datetime.datetime.now().second} secs at {i}')

#     send_ascii_command(f'jog off {_motors[0]} {_motors[1]}')
#     print((get_elevation(), get_azimuth()))
#     print(_move_queue[-1])
#     send_ascii_command(f'jog abs {_motors[0]}{_move_queue[-1][0]} {_motors[1]}{_move_queue[-1][1]}')
#     _move_queue = []


def velocity_steer_run():
    global _move_queue
    accel, decel, stp, vel = get_motion_parameters()
    sleep(set_el_az(_move_queue[0][0], _move_queue[0][1]))    
    send_ascii_command(f'jog acc x{accel} y{accel} z{accel} a{accel}')
    send_ascii_command(f'jog dec x{decel} y{decel} z{decel} a{decel}')
    send_ascii_command(f'jog vel x{vel} y{vel} z{vel} a{vel}')

    for i, move in enumerate(_move_queue[1:len(_move_queue) - 1]): #_move_queue must start with the starting position
        i = i + 1
        vec = (move[0] - _move_queue[i-1][0], move[1] - _move_queue[i-1][1])
        #vec = (move[0] - get_elevation(), move[1] - get_azimuth()) # for whatever reason this doesn't work at all but the previous works ok
        mag = sqrt(vec[0]**2 + vec[1]**2)
        vec = (vec[0] / mag*vel, vec[1] / mag*vel)
        send_ascii_command(f'jog vel {_motors[0]}{abs(round(vec[0], 4))} {_motors[1]}{abs(round(vec[1], 4))}')
        #send_ascii_command(f'jog abs {_motors[0]}{move[0]} {_motors[1]}{move[1]}')
        send_ascii_command(f'jog {"fwd" if vec[0] > 0 else "rev"} {_motors[0]}')
        send_ascii_command(f'jog {"fwd" if vec[1] > 0 else "rev"} {_motors[1]}')
        
        next_vec = (_move_queue[i+1][0] - move[0], _move_queue[i+1][1] - move[1])
        mag = sqrt(next_vec[0]**2 + next_vec[1]**2)
        next_vec = (next_vec[0] / mag * vel, next_vec[1] / mag * vel)
        #d_vec = (next_vec[0]**2 - vec[0]**2, next_vec[1]**2 - vec[1]**2)
        d_vec = (next_vec[0] - vec[0], next_vec[1] - vec[1])
        criterion = max(abs(d_vec[0]), abs(d_vec[1])) > .1
        if (abs(vec[0]) > abs(vec[1])):#wanted to use d_vec only but that was running into a vanishing gradient type situation when both were small 
            while ((el := get_elevation()) > move[0] - d_vec[0]/2/accel) if vec[0] < 0 else (el := get_elevation()) < move[0] - d_vec[0]/2/accel:
                pass
                #print(f'Waiting until {round(move[0] - d_vec[0]/accel, 2)}el at {el} at {datetime.datetime.now().second} secs at {i}')
        else:
            while ((az := get_azimuth()) > move[1] - d_vec[1]/2/accel) if vec[1] < 0 else (az := get_azimuth()) < move[1] - d_vec[1]/2/accel:
                pass
                #print(f'Waiting until {round(move[1] - d_vec[1]/accel, 2)}az at {az} at {datetime.datetime.now().second} secs at {i}')

    send_ascii_command(f'jog off {_motors[0]} {_motors[1]}')
    print((get_elevation(), get_azimuth()))
    print(_move_queue[-1])
    send_ascii_command(f'jog abs {_motors[0]}{_move_queue[-1][0]} {_motors[1]}{_move_queue[-1][1]}')
    _move_queue = []



# def run_moves(step_interp_factor=5, time_per_step=.1):
#     global _move_queue
#     accel, decel, stp, vel = get_motion_parameters()
#     def sign(n):
#         if(n == 0):
#             return 0
#         return n / abs(n)
#     set_el_az(_move_queue[0][0], _move_queue[0][1])\
    
#     send_ascii_command('DIM LA(2)')
#     send_ascii_command(f'DIM LA0({len(_move_queue)})')
#     send_ascii_command(f'DIM LA1({len(_move_queue)})')

#     for i, move in enumerate(_move_queue): #_move_queue must start with the starting position
#         send_ascii_command(f'LA0({i})={move[0]}')
#         send_ascii_command(f'LA1({i})={move[1]}')

#     send_ascii_command(f'CAM DIM {_motors[0]}1 {_motors[1]}1')
#     send_ascii_command(f'CAM SEG {_motors[0]}({0},{len(_move_queue)*step_interp_factor},LA0)')
#     send_ascii_command(f'CAM SEG {_motors[1]}({1},{len(_move_queue)*step_interp_factor},LA1)')
#     send_ascii_command('p0=0')
#     send_ascii_command(f'CAM SRC {_motors[0]} p0 {_motors[1]} p0')
#     PPU0 = 2**19 * _ratios[0] / 360 # pulses per unit
#     PPU1 = 2**19 * _ratios[1] / 360
#     send_ascii_command(f'CAM SCALE {_motors[0]}(1/{round(PPU0)}) {_motors[1]}(1/{round(PPU1)})')
    
#     send_ascii_command(f'CAM ON {_motors[0]} {_motors[1]}')

#     for i in range(len(_move_queue)*step_interp_factor):
#         send_ascii_command(f'p0={i}')
#         time = datetime.datetime.now()
#         while (datetime.datetime.now() - time).microseconds < time_per_step/step_interp_factor * 1000000:
#             pass


#     print((get_elevation(), get_azimuth()))
#     print(_move_queue[-1])
#     _move_queue = []
#     send_ascii_command('CAM OFF X Y Z A')
#     send_ascii_command('CLEAR')
#     send_ascii_command('CAM CLEAR')


# def back_to_normal():
#     send_ascii_command(f'jog vel {_motors[0]}{_vel} {_motors[1]}{_vel}')
#     send_ascii_command(f'jog abs {_motors[0]}0 {_motors[1]}0')
#     return max(abs(get_elevation() / _vel), abs(get_azimuth() / _vel))

startup()
switch_to_el_az()
set_motion_parameters(10, 10, 10, 5)
set_el_az(0, 20)
for i in range(361):
    add_move((-20 * sin(i / 360 * 2 * pi), 20 * cos(i / 360 * 2 * pi)))

program_moves()

for i in range(50):
    run_moves()
    sleep(35)