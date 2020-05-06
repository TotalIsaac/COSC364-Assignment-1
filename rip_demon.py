import socket
import sys
import os.path
import json

def rip_demon(filename):
    """RIP demon. Handles basically everything"""
    router_id, timers = "", ""
    input_ports, outputs = [], []
    receive_ports = {}
    routing_table = {} # key by router-id, value [port (next hop), metric, timer?] 
    
    #Run the config
    router_id, timers = config(filename, router_id, input_ports, outputs, timers)

    #Initial table
    for router in outputs:
        routing_table[router[2]] = [router[0], router[1]]

    #Create UDP sockets for each input port
    for port in input_ports:
        sending_packet(port, "127.0.0.1")  
        receive_ports[port] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receive_ports[port].bind("127.0.0.1", port)
        
    while True:
        #Check each port for data.
        #If data there, compare routing tables and update if needed
        for port in receive_ports:
            port.listen()

        #Send data about own table  
    


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
        router_id= int(setup["router-id"][0])

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
        if not (int(outs[0]) >= 1024 or int(outs[0]) <= 64000):
            print("input-port for output must be between 1024 and 64000")
            sys.exit()
        elif int(outs[0]) in input_ports:
            print("output port values should not be listed in input-port values")
            sys.exit()
        elif int(outs[1]) < 0:
            print("metric values must be non-negative")
            sys.exit()
        elif int(outs[2]) < 1 or int(outs[2]) > 64000:
            print("Neighbouring router id must be between 1 and 64000")
            sys.exit()
        else:
            outputs.append(outs)
    
    #Checks timer field is present and whether it is of the required ratio
    if "timer" in setup.keys():
        if int(setup["timer"][0]) / int(setup["timer"][1]) != 6:
            print("Timeout/periodic ration must equal 6")
            sys.exit()
            
    return router_id, timers

def sending_packet(port, ip):

    #Send UDP packet that contains routing information to other neighbor        
    try: 
        sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        print "Socket successfully created"
    except socket.error as err: 
        print "socket creation failed with error %s" %(err)
        
    # connecting to the server 
    sckt.connect(ip, port)     
    

def packet_prep(rt_table, rt_id):
    """Prepares a RIP packet into a bytearray. Takes the routing table and 
    the id of the sending router"""
    bin_table = dict_to_binary(rt_table)
    
    packet = bytearray()
    packet.append(2) #Command is always a response (2) for this assignment. 
    packet.append(2) #Version is always 2
    packet.append(rt_id >> 8)
    packet.append(rt_id & 0xFF)
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


def distance_vec(table, recv_table, metric, recv_port):
    """Compares routes between the main routing table, and those received. Checks if a 
    received route is more cost effective. If so, it replaces that route in the main table."""
    
    for route in recv_table:
        if route not in table:
            met = recv_table[route][1] + metric
            if met > 16: #16 is infinity as far as RIP is concerned
                met = 16
            table[route] = [recv_port, met] 
        elif (recv_table[route][1] + metric) < (table[route][1]):
            table[route] = [recv_port, recv_table[route][1] + metric]


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