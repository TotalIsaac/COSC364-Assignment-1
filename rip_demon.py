import socket
import sys
import os.path

def rip_demon(filename):
    """RIP demon. Handles basically everything"""
    router_id, timers = "", ""
    input_ports, outputs = [], []
    
    #Run the config
    router_id, timers = config(filename, router_id, input_ports, outputs, timers)

    
    


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

    #Checks input ports fall between required value, and that they occur no more than once.
    #If these requirements pass, it is added to the list of input_ports
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
        
    #Checks port falls within required values and isn't in input ports.
    #Ensures metrics are non-negative
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
            
    #Send UDP packet that contains routing information to other neighbor        
    opened_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    opened_socket.sendto(router_id, ("127.0.0.1", 5005))
    return router_id, timers



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