
import time
import arduino_controller.arduino_led_controller as als
import requests


print ('Socket created')
#Wird beim Ausfuehren des Programms nur der Speicherort und der Programmname in der Shell angezeigt, so sind die IP Adressen des Programms und der dryve D1 nicht uebereinstimmend
#When executing the program and the shell displays the storing folder and the program name, the set IP address in the program and the dryve D1 doesn't match

# Digitale Eingänge 60FDh
# digital inputs
DInputs = [0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4]  
DInputs_array = bytearray(DInputs)
print(DInputs_array)


# Statusword 6041h
# Status request
status = [0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2]
status_array = bytearray(status)
print(status_array)

# Controlword 6040h
# Command: Shutdown
shutdown = [0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 6, 0]
shutdown_array = bytearray(shutdown)
print(shutdown_array)

# Controlword 6040h
# Command: Switch on
switchOn = [0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 7, 0]
switchOn_array = bytearray(switchOn)
print(switchOn_array)

# Controlword 6040h
# Command: enable Operation
enableOperation = [0, 0, 0, 0, 0, 15, 0, 43,13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 15, 0]
enableOperation_array = bytearray(enableOperation)
print(enableOperation_array)

# Controlword 6040h
# Command: stop motion
stop = [0, 0, 0, 0, 0, 15, 0, 43,13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 15, 1]
stop_array = bytearray(stop)
print(stop_array)

# Controlword 6040h
# Command: reset dryve
reset = [0, 0, 0, 0, 0, 15, 0, 43,13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 0, 1]
reset_array = bytearray(reset)
print(reset_array)

# Controlword 6040h
# Command: fault reset
fault_reset = [0, 0, 0, 0, 0, 15, 0, 43,13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 128, 0]
fault_reset_array = bytearray(fault_reset)
print(fault_reset_array)
# Variablen einen Startwert geben
# Variables start value
start = 0
ref_done = 0
error = 0

#Definition der Funktion zum Senden und Empfangen von Daten
#Definition of the function to send and receive data 
def sendCommand(socket,data):
    try:
        #Socket erzeugen und Telegram senden
        #Create socket and send request
        socket.send(data)
        res = socket.recv(24)
        #Ausgabe Antworttelegram 
        #Print response telegram
        print(list(res))
        if list(res)==[]:
            return "DISCONNECTED"
        return list(res)
    except:
        return False

#Shutdown Controlword senden und auf das folgende Statuswort pruefen. Pruefung auf mehrer Statuswords da mehrere Szenarien siehe Bit assignment Statusword, data package im Handbuch 
#sending Shutdown Controlword and check the following Statusword. Checking several Statuswords because of various options. look at Bit assignment Statusword, data package in user manual 
def set_shdn(socket):
    timer = 2
    calc = 0
    try:
        sendCommand(socket,reset_array)
        sendCommand(socket,shutdown_array)
        while (sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33, 6]
            and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33, 22]
            and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33, 2]):
            print("wait for shdn")
            time.sleep(1)
            if calc >= timer:
                return False
            calc = calc+1
        return True
    except:
        return False


def get_homing_status(socket):
    read_command = bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 32, 20, 0, 0, 0, 0, 2, 0, 0])
    response = sendCommand(socket,read_command)
    if response:
        if len(response) >= 21:
            status_value = response[-2]
            if status_value & 1:
                return True
    return False


#Switch on Disabled Controlword senden und auf das folgende Statuswort pruefen. Pruefung auf mehrer Statuswords da mehrere Szenarien siehe Bit assignment Statusword, data package im Handbuch 
#sending Switch on Disabled Controlword and check the following Statusword. Checking several Statuswords because of various options. look at Bit assignment Statusword, data package in user manual 
def set_swon(socket):
    timer = 2
    calc = 0
    try:
        sendCommand(socket,switchOn_array)
        while (sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35, 6]
            and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35, 22]
            and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35, 2]):
            print("wait for sw on")
            time.sleep(1)
            if calc >= timer:
                return False
            calc = calc+1
        return True
    except:
        return False


#Operation Enable Controlword senden und auf das folgende Statuswort pruefen. Pruefung auf mehrer Statuswords da mehrere Szenarien siehe Bit assignment Statusword, data package im Handbuch 
#Operation Enable Controlword and check the following Statusword. Checking several Statuswords because of various options. look at Bit assignment Statusword, data package in user manual 
def set_op_en(socket):
    timer = 2
    calc = 0
    try:
        sendCommand(socket,enableOperation_array)
        while (sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 6]
            and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
            and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 2]):
            print("wait for op en")

            time.sleep(1)
            if calc >= timer:
                return False
            calc = calc+1
        return True
    except:
        return False


def init(socket):
    try:
        set_mode(socket,1)
        sendCommand(socket,reset_array)
        set_shdn(socket)
        set_swon(socket)
        set_op_en(socket)
        return True
    except:
        return False

def set_mode(socket,mode):
    timer = 2
    calc = 0
    try:
        sendCommand(socket,bytearray([0, 0, 0, 0, 0, 14, 0, 43, 13, 1, 0, 0, 96, 96, 0, 0, 0, 0, 1, mode]))
        while (sendCommand(socket,bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 97, 0, 0, 0, 0, 1])) != [0, 0, 0, 0, 0, 14, 0, 43, 13, 0, 0, 0, 96, 97, 0, 0, 0, 0, 1, mode]):
            print("wait for mode")
            time.sleep(1)
            if calc >= timer:
                return False
            calc = calc+1
        return True
    except:
        return False

def homing_with_search(socket):
    try:
        if sendCommand(socket,enableOperation_array):
            #6060h Modes of Operation
            if set_mode(socket,6):
                # 6092h_01h Feed constant Subindex 1 (Feed)
                if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 1, 0, 0, 0, 4, 24, 21, 0, 0])):
                    # 6092h_02h Feed constant Subindex 2 (Shaft revolutions)
                    if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 2, 0, 0, 0, 4, 1, 0, 0, 0])):
                        # 6099h_01h Homing speeds Switch
                        if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 153, 1, 0, 0, 0, 4, 112, 23, 0, 0])):
                            # 6099h_02h Homing speeds Zero
                            if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 153, 2, 0, 0, 0, 4, 112, 23, 0, 0])):
                                # 609Ah Homing acceleration
                                if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 154, 0, 0, 0, 0, 4, 160, 134, 1, 0])):
                                    # 6040h Controlword
                                    if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0])):
                                        while (sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
                                            and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]
                                            and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 34]
                                            and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 2]):
                                                if sendCommand(socket,DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]:
                                                    break
                                                time.sleep(0.1)
                                                print ("Homing")
                                        return True
    except:
        return False

def homing_without_search(socket):
    try:
        if sendCommand(socket,enableOperation_array):
            #6060h Modes of Operation
            if set_mode(socket,6):
                # 6092h_01h Feed constant Subindex 1 (Feed)
                if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 1, 0, 0, 0, 4, 24, 21, 0, 0])):
                    # 6092h_02h Feed constant Subindex 2 (Shaft revolutions)
                    if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 2, 0, 0, 0, 4, 1, 0, 0, 0])):
                        # 6099h_01h Homing speeds Switch
                        if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 153, 1, 0, 0, 0, 4, 112, 23, 0, 0])):
                            # 6099h_02h Homing speeds Zero
                            if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 153, 2, 0, 0, 0, 4, 112, 23, 0, 0])):
                                # 609Ah Homing acceleration
                                acceleration = 100
                                acceleration_bytes = acceleration.to_bytes(4, byteorder='little', signed=True)
                                if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 154, 0, 0, 0, 0, 4, *acceleration_bytes])):

                                    #Start Homing
                                    sendCommand(socket,bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0]))

                                    while (sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
                                        and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]
                                        and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 34]
                                        and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 2]):
                                            #Wenn der Stoptaster gedrückt wird soll die Kette unterbrechen
                                            #If the StopButton is pushed the loop breaks
                                            if sendCommand(socket,DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]:
                                                break
                                            time.sleep(0.1)
                                            print ("Homing")
                                    return True
    except:
        return False

def move_to_position(socket,target_position, velocity, acceleration, deceleration, stop_event):  
    try: 
        if set_mode(socket,1):
            velocity_bytes = velocity.to_bytes(4, byteorder='little', signed=True)
            if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 129, 0, 0, 0, 0, 4, *velocity_bytes])):
                sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 108, 0, 0, 0, 0, 4, *velocity_bytes]))
                time.sleep(0.1)
                acceleration_bytes = acceleration.to_bytes(4, byteorder='little', signed=True)
                if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 131, 0, 0, 0, 0, 4, *acceleration_bytes])):
                    time.sleep(0.1)
                    deceleration_bytes = deceleration.to_bytes(4, byteorder='little', signed=True)
                    if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 132, 0, 0, 0, 0, 4, *deceleration_bytes])):
                        time.sleep(0.1)
                        target_position_bytes = target_position.to_bytes(4, byteorder='little', signed=True)
                        if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 122, 0, 0, 0, 0, 4, *target_position_bytes])):
                            time.sleep(0.1)
                            sendCommand(socket,enableOperation_array)
                            if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0])):
                                print("Motion started")
                                time.sleep(0.1)
                                while (sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
                                    and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]
                                    and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 18]
                                    and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 16]):
                                    if stop_event is None:
                                        stop = False
                                    else:
                                        stop = stop_event.is_set()
                                    if sendCommand(socket,DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0] or stop:
                                        print("Motion stopped by user")
                                        stop_event.clear()
                                        sendCommand(socket,stop_array)
                                        break
                                    time.sleep(0.2)
                                    print("Motion in progress")
                                return True
        sendCommand(socket,stop_array)
    except:
        sendCommand(socket,stop_array)
        return False

def jog_move(socket, velocity=400, stop_event=None):  
    try:
        if set_mode(socket,3):
            velocity_bytes = velocity.to_bytes(4, byteorder='little', signed=True)
            if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 129, 0, 0, 0, 0, 4, *velocity_bytes])):
                sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 108, 0, 0, 0, 0, 4, *velocity_bytes]))
                sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 255, 0, 0, 0, 0, 4, *velocity_bytes]))
                time.sleep(0.2)                
                acceleration = 4000
                acceleration_bytes = acceleration.to_bytes(4, byteorder='little', signed=True)
                if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 131, 0, 0, 0, 0, 4, *acceleration_bytes])):
                    time.sleep(0.2)
                deceleration = 4000
                deceleration_bytes = deceleration.to_bytes(4, byteorder='little', signed=True)
                if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 132, 0, 0, 0, 0, 4, *deceleration_bytes])):
                        time.sleep(0.2)
                if sendCommand(socket,enableOperation_array):
                    time.sleep(0.2)
                    if sendCommand(socket,bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0])):
                        print("Motion started")
                        while (sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
                            and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 18]
                            and sendCommand(socket,status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]):
                            stop = stop_event.is_set()
                            if sendCommand(socket,DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0] or stop:
                                print("Motion stopped by user")
                                if stop_event is None:
                                    stop = False
                                else:
                                    stop = stop_event.is_set()
                                sendCommand(socket,stop_array)
                                break
                            time.sleep(0.2)
                            print("Motion in progress")
                        return True
            sendCommand(socket,stop_array)
    except:
        sendCommand(socket,stop_array)
        return False 
        
def error_checking(socket):    
    try:      
        if (sendCommand(socket,status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]
            or sendCommand(socket,status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]
            or sendCommand(socket,status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 34]
            or sendCommand(socket,status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 2] ):
                return False
        else: 
            return True
    except:
        return False


def jog_stop(socket):
    try:
        if sendCommand(socket,stop_array):
            return True
    except:
        return False

prev_command = None

def get_actual_position(socket):

    read_command = bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 0x60, 0x64, 0x00, 0, 0, 0, 2, 0, 0])
    
    # Отправка команды
    response = sendCommand(socket,read_command)
    
    # Проверка ответа (ожидаем данные в последних 4 байтах)
    if len(response) >= 15:
        position_bytes = response[-2:]  # Берем последние 4 байта как значение позиции
        position_value = int.from_bytes(position_bytes, byteorder='little', signed=True)
        return int(position_value)
    else:
        print("Error: Invalid response length.")
        return False

def get_from_web_command(socket,command):
    if command == "ACTUAL_POSITION":
        val = get_actual_position(socket)
        return val
    
    elif command == "REFERENCE_STATUS":
        if get_homing_status(socket):
            return True
        
    elif command == "READY_STATUS":
        if check_ready_status(socket):
            return True
    return False
        
def check_ready_status(socket):
    try:
        if not get_homing_status(socket):
            return False
        if not error_checking(socket):
            return False
        return True
    except:
        return False    
    
def start_from_web_command(socket,command, led=False, value=None,velocity=None,stop_event=None):
    if (command != "REFERENCE") and (command != "RESET"):
        if not check_ready_status(socket):
            return False
        
    if command == "ABS":
        try:
            if led:
                als.send_command(3)
            if get_homing_status(socket) == True:
                if move_to_position(socket,value,velocity,velocity,velocity,stop_event):
                    return True
            return False
        except:
            return False
        
    if command == "JOG_UP":
        try:
            if led:
                als.send_command(3)
            print("JOG_UP")
            jog_move(socket, velocity, stop_event)
            return True
        except:
            return False

    if command == "JOG_DOWN":
        try:
            if led:
                als.send_command(3)
            print("JOG_DOWN")
            jog_move(socket, -velocity, stop_event)
            return True
        except:
            return False



    if command == "REFERENCE":
        try:
            if led:
                als.send_command(5)
            if set_shdn(socket):
                if homing_without_search(socket):
                    if init(socket):
                        if get_homing_status(socket):
                            return True
            return False
        except:
            return False
                
    if command == "RESET":
        try:
            if led:
                als.send_command(5)
            if set_mode(socket,1):
                if sendCommand(socket,reset_array):
                    time.sleep(0.2)
                    if sendCommand(socket,fault_reset_array):
                        time.sleep(0.2)
                        if init(socket):
                            time.sleep(5)
                            return True
        except:
            return False
