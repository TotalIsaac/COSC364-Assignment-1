import socket
import sys
import os.path
import json
import select
import time
import copy

def rip_demon(filename):
    """RIP demon. Handles basically everything"""
    router_id = ""
    input_ports, outputs, timers = [], [], []
    recv_ports = []
    routing_table = {} # key by router-id, value [port (next hop), metric, timer?] 
    curr_time = time.time()
    
    #Run the config
    router_id = config(filename, router_id, input_ports, outputs, timers)

    #Initial table
    for router in outputs:
        routing_table[str(router[2])] = [router[0], router[1], time.time()]

    #Create UDP sockets for each input port
    for port in input_ports:
        new_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        new_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        new_socket.bind(("127.0.0.1", port))
        recv_ports.append(new_socket)

    send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    while True:
        #select.select() returns three list objects. From what I've read, [0][0] is the
        #socket we want

        serv = select.select(recv_ports, [], [], 3)
        if len(serv[0]) > 0:
            ready_server = serv[0][0]
            message, addr = ready_server.recvfrom(4096)
            recv_table, recv_rt_id = read_packet(message)
            print(routing_table)
            if distance_vec(routing_table, recv_table, routing_table[str(recv_rt_id)][1], recv_rt_id, router_id):
                send_pack(routing_table, router_id, outputs, send_socket, input_ports)
         
        #Send update after specified time has elapsed
        if(time.time() - curr_time >= timers[1]):
            send_pack(routing_table, router_id, outputs, send_socket, input_ports)
            curr_time = time.time()
        
        ###TODO Deal with timeouts, removing invalid entries in the routing table,
        ### garbage collection, etc 
        for route in routing_table:
            if (time.time() - routing_table[route][2] >= timers[0]):
                routing_table[route][1] = 16
                routing_table[route][2] = time.time()
                send_pack(routing_table, router_id, outputs, send_socket, input_ports)



    
def send_pack(routing_table, router_id, outputs, send_socket, inputs):
    """Preps a packet and sends it to each reachable output"""
    packet = packet_prep(routing_table, router_id)
    for out in outputs:
        send_table = copy.deepcopy(routing_table)
        for route in routing_table:
            if send_table[route][0] == int(out[0]):
                send_table[route][1] = 16
                send_table[str(router_id)] = [inputs[0], out[1], time.time()]
                packet = packet_prep(send_table, router_id)
            else:
                send_table[str(router_id)] = [inputs[0], out[1], time.time()]
                packet = packet_prep(send_table, router_id)
        send_socket.sendto(packet, ("127.0.0.1", int(out[0])))

def config(filename, router_id, input_ports, outputs, timers):
    """Reads the provided config file and performs the required checks"""

    setup = {}
    
    #If the file doesn't exist, exit
    if not os.path.isfile(filename):
        print("There is no config file with this name")
        sys.exit()

    #Read the config file and store info in dict setup
    with open(filename, 'r') as f:
        for line in f:
            items = line.split()
            if(items[0][:2] != '//'):
                key, values = items[0], items[1:]
                setup[key] = values

    #Check the require elements are present in the config
    if ("router-id" or "input-ports" or "outputs") not in setup:
        print("Missing required elements in the config file")
        sys.exit()
    
    #Check router-id is within required bounds
    if int(setup["router-id"][0]) > 64000 or int(setup["router-id"][0]) < 1:
        print("router-id must be between 1 and 64000")
        sys.exit()
    else:
        router_id= setup["router-id"][0]

    #Checks input ports fall meet requirements, then adds them to list.
    for port in setup["input-ports"]:
        port = int(port)
        if  port < 1024 or port > 64000:
            print("input-ports must be between 1024 and 64000")
            sys.exit()
        else:
            if port in input_ports:
                print("input-port numbers must occur no more than once")
                sys.exit()
            else:
                input_ports.append(port)
        
    #Checks output port falls within required values and isn't in input ports.
    for outs in setup["outputs"]:
        outs = outs.split('-')
        for i in range(len(outs)):
            outs[i] = int(outs[i])
        if not (outs[0] >= 1024 or outs[0] <= 64000):
            print("input-port for output must be between 1024 and 64000")
            sys.exit()
        elif outs[0] in input_ports:
            print("output port values should not be listed in input-port values")
            sys.exit()
        elif outs[1] < 0:
            print("metric values must be non-negative")
            sys.exit()
        elif outs[2] < 1 or outs[2] > 64000:
            print("Neighbouring router id must be between 1 and 64000")
            sys.exit()
        else:
            outputs.append(outs)
    
    #Checks timer field is present and whether it is of the required ratio
    if "timer" in setup.keys():
        if int(setup["timer"][0]) / int(setup["timer"][1]) != 6:
            print("Timeout/periodic ration must equal 6")
            sys.exit()
        else:
            timers.append(int(setup["timer"][0]))
            timers.append(int(setup["timer"][1]))
        
    return router_id  
    
def packet_prep(rt_table, rt_id):
    """Prepares a RIP packet into a bytearray. Takes the routing table and 
    the id of the sending router"""
    bin_table = dict_to_binary(rt_table)
    
    packet = bytearray()
    packet.append(2) #Command is always a response (2) for this assignment. 
    packet.append(2) #Version is always 2
    packet.append(int(rt_id) >> 8)
    packet.append(int(rt_id) & 0xFF)
    packet += bin_table

    return packet

def read_packet(packet):
    """Reads a received packet. Runs through checks and returns the routing table & sender info"""
    command = packet[0]
    version = packet[1]
    rt_id = packet[2] << 8 | packet[3]
    table = binary_to_dict(packet[4:])

    if command != 2 or version != 2:
        return 1
    elif int(rt_id) > 64000 or int(rt_id) < 1:
        return 1
    else:
        return table, rt_id

def dict_to_binary(dct):
    """Converts a dict to binary"""
    s = json.dumps(dct).encode('utf-8')
    return s

def binary_to_dict(binary):
    """Converts binary to a dict"""
    d = json.loads(binary.decode('utf-8'))  
    return d

def distance_vec(table, recv_table, metric, recv_rt, self_rt_id):
    """Compares routes between the main routing table, and those received. Checks if a 
    received route is more cost effective. If so, it replaces that route in the main table."""
    change = False 
    recv_port = table[str(recv_rt)][0] 
    #Update time when receiving from directly connected routers
    if str(recv_rt) in table and table[str(recv_rt)][1] == metric:
        table[str(recv_rt)][2] = time.time()

    for route in recv_table:
        if route == self_rt_id:
            pass #Ignore entry routing to self
        elif route not in table:
            met = int(recv_table[route][1]) + int(metric)
            if met > 16: #16 is infinity as far as RIP is concerned
                met = 16
            table[route] = [recv_port, met, time.time()] 
            change = True
        elif (recv_table[route][1] + metric) < (table[route][1]):
            table[route] = [recv_port, recv_table[route][1] + metric, time.time()]
            change = True
        elif (recv_table[route][1] + metric) == (table[route][1]) and (recv_port == table[route][0]):
            table[route][2] = time.time()
        elif table[route][0] == table[str(recv_rt)][0]:
            met = int(recv_table[route][1]) + int(metric)
            if met > 16: #16 is infinity as far as RIP is concerned
                met = 16
            table[route] = [recv_port, met, time.time()] 
            change = True

    
    return change #If there is a change to the routing table, return true to trigger update

def main():
    """Main. Running the file from command line will start it here"""

    #Check there is exactly one argument provided
    if len(sys.argv[1:]) != 1:
        print("Exactly 1 argument is required")
        sys.exit()
    else:
        filename = sys.argv[1] #Grab the filename from the 1 provided argument
        rip_demon(filename) #Start the demon

if __name__ == "__main__":
    main()