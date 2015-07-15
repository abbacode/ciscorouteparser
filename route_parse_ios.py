import re
import csv
import ipaddress

__version__ = 1.0

routes_key = {"C"     : "Connected",
              "S"     : "Static",
              "R"     : "RIP",
              "B"     : "BGP",
              "B*"    : "BGP*",
              "D"     : "EIGRP",
              "D*"    : "EIGRP*",
              "D EX"  : "EIGRP External",
              "O"     : "OSPF",
              "O*"    : "OSPF*",
              "O*E1"  : "OSPF* Candidate Default",
              "O*E2"  : "OSPF* Candidate Default",
              "O E1"  : "OSPF External 1",
              "O E2"  : "OSPF External 2",
              "O IA"  : "OSPF Inter-Area",
              "O N1"  : "OSPF NSSA External Type 1",
              "O N2"  : "OSPF NSSA External Type 2",
              "L"  : "Local",
              "i"  : "IS-IS",
              "i su"  : "IS-IS Summary",
              "i L1"  : "IS-IS Level-1",
              "i L2"  : "IS-IS Level-2",
              "i ia"  : "IS-IS Inter-Area",
              "*"  : "Candidate Default"}

# Each route will have the following values
class Route_Template(object):
    def __init__(self):
        self.route = {}
        self.protocol = []
        self.metric = []
        self.next_hop = []
        self.age = []
        self.interface = []
    def __repr__(self):
        return str(self.route)

# The main code structure
class RouteParse(object):
    def __init__(self):
        self.route_table = {}
        self.Read_File()
        self.Generate_Output_To_File()

    # Retrieve a route object if it exists
    def Get_Route_Object(self,target_route):
        for route in self.route_table:
            if target_route in route:
                return self.route_table[route]
        return None

    # If the regular expression picked up a valid route, extract the values into a temporary dictionary
    def Get_Route_Values_From_Match(self,matchObj):
        values = {}
        for keyword, value in vars(Route_Template()).items():
            if keyword in matchObj.groupdict():
                val =  str(matchObj.group(keyword).strip())
                values[keyword] = val
            else:
                values[keyword] = "N/A"
        return values

    # Create a new route object using the values from the temporary dictionary
    def Create_New_Route(self,match):
        route = self.Get_Route_Values_From_Match(match)
        route_prefix = route["route"]
        if not self.Get_Route_Object(route_prefix):
            NewRoute = Route_Template()
            NewRoute.route = route["route"]
            NewRoute.protocol.append(route["protocol"])
            NewRoute.metric.append(route["metric"])
            NewRoute.next_hop.append(route["next_hop"])
            NewRoute.interface.append(route["interface"])
            NewRoute.age.append(route["age"])
            self.route_table[NewRoute.route] = NewRoute

    # Search the route for an ECMP pattern and then update the route object if it is found
    def Add_ECMP_Route(self,previous_route,line):
        route = self.Get_Route_Object(previous_route)
        ecmp_patterns = [r'(?P<metric>\[.*\/.*\]) via (?P<next_hop>.*), (?P<age>.*), (?P<interface>.*)', \
                        r'(?P<metric>\[.*\/.*\]) via (?P<next_hop>.*), (?P<age>.*)']
        for pattern in ecmp_patterns:
            match = re.search(pattern,line)
            if match:
                route.protocol.append(route.protocol[0])
                route.metric.append(match.group('metric').strip())
                route.next_hop.append(match.group('next_hop').strip())
                route.age.append(match.group('age').strip())
                try:
                    route.interface.append(match.group('interface').strip())
                except IndexError:
                    route.interface.append("N/A")
                break

    def Get_Host_Range(self,subnet):
        try:
            range = ipaddress.ip_network(subnet)
            return range[1],range[-2]
        except ValueError:
            return "error", "error"
        except IndexError: # Handles /32
            return range[0], ""


    def Generate_Output_To_File(self):
        try:
            with open('routes.csv', 'w', newline='') as csv_file:
                spamwriter = csv.writer(csv_file, delimiter=',',
                                                  quotechar='|',
                                                  quoting=csv.QUOTE_MINIMAL)
                spamwriter.writerow(['Route', 'Protocol','Metric','Next Hop','Age','Interface','From Range','To Range'])

                for entry in sorted(self.route_table):
                    route = self.Get_Route_Object(entry)
                    first_ip, last_ip = self.Get_Host_Range(route)
                    for no in range(len(route.protocol)):
                        spamwriter.writerow([route.route,
                                             route.protocol[no],
                                             route.metric[no],
                                             route.next_hop[no],
                                             route.age[no],
                                             route.interface[no],
                                             first_ip,
                                             last_ip])
            print ("  -- Output saved to 'routes.csv'")
        except:
            print ("  -- Unable to write to routes.csv, if the file is already open close it.")

    def Read_File(self):
        start_processing_routes = False
        invalid_phrases = ["variably","subnetted"]

        with open("routes.txt","r") as route_file:
            for line in route_file:
                #-----------------------
                # Ignore certain input
                #-----------------------
                if line.count(' ') < 2:
                    continue
                if any(x in line for x in invalid_phrases):
                    continue
                if "Gateway" in line:
                    start_processing_routes = True
                    continue

                line = line.strip().replace("\n","")
                if start_processing_routes:
                    #---------------------------------------
                    # Define all the possible regex patterns
                    #---------------------------------------
                    # Line 1. BGP
                    # Line 2. IGP (OSPF,EIGRP etc)
                    # Line 3. Static routes
                    # Line 4. Connected/local routes
                    #---------------------------------------
                    patterns = [r'(?P<protocol>[a-zA-Z] ..) (?P<route>.*) (?P<metric>.*) via (?P<next_hop>.*), ?(?P<age>.*), ?(?P<interface>.*)', \
                                r'(?P<protocol>[a-zA-Z]..) (?P<route>.*) (?P<metric>.*) via (?P<next_hop>.*), ?(?P<age>.*), ?(?P<interface>.*)', \
                                r'(?P<protocol>[a-zA-Z]) (?P<route>.*) is a summary, (?P<age>.*), (?P<interface>.*)', \
                                r'(?P<protocol>[a-zA-Z]..) (?P<route>.*) is a summary, (?P<age>.*), (?P<interface>.*)', \
                                r'(?P<protocol>B.*|B\*.*) (?P<route>.*) (?P<metric>.*) via (?P<next_hop>.*), (?P<age>.*)', \
                                r'(?P<protocol>S.*|S\*.*) (?P<route>.*) (?P<metric>.*) via (?P<next_hop>.*)', \
                                r'(?P<protocol>C.*|L.*) (?P<route>.*) is directly connected, (?P<interface>.*)']
                    #-----------------------------------------------------
                    # Cycle through all the patterns and grab the matches
                    #-----------------------------------------------------
                    valid_route_entry = False
                    for regex in patterns:
                        match = re.search(regex,line)
                        if match:
                            self.Create_New_Route(match)
                            last_route = match.group('route').strip()
                            valid_route_entry = True
                            break
                    if not valid_route_entry:
                        self.Add_ECMP_Route(last_route, line)


print ("Cisco IOS Route Parser version: '{}'".format(__version__))
c = RouteParse()


