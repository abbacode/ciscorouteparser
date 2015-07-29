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
class Route(object):
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
class Code(object):
    def __init__(self):
        self.route_table = {}
        self.read_file()
        self.generate_output_to_file()

    # Retrieve a route object if it exists
    def get_route(self,route):
        return self.route_table.get(route)

    # If the regular expression picked up a valid route, extract the values into a temporary dictionary
    def get_match_values(self,match):
        values = {}
        for keyword, value in vars(Route()).items():
            if keyword in match.groupdict():
                val =  str(match.group(keyword).strip())
                values[keyword] = val
            else:
                values[keyword] = ""
        return values

    # Create a new route object using the values from the temporary dictionary
    def create_route(self,match):
        match_values = self.get_match_values(match)
        route_prefix = match_values["route"]
        existing_route = self.get_route(route_prefix)

        if not existing_route:
            new_route = Route()
            new_route.route = match_values["route"]
            new_route.protocol.append(match_values["protocol"])
            new_route.metric.append(match_values["metric"])
            new_route.next_hop.append(match_values["next_hop"])
            new_route.interface.append(match_values["interface"])
            new_route.age.append(match_values["age"])
            self.route_table[route_prefix] = new_route

    # Search the route for an ECMP pattern and then update the route object if it is found
    def add_ecmp_route(self,route,string_to_search):
        parent_route = self.get_route(route)
        ecmp_patterns = [
            r'(?P<metric>\[.*\/.*\]) via (?P<next_hop>.*), (?P<age>.*), (?P<interface>.*)', \
            r'(?P<metric>\[.*\/.*\]) via (?P<next_hop>.*), (?P<age>.*)'
        ]
        for pattern in ecmp_patterns:
            match = re.search(pattern,string_to_search)
            if match:
                parent_route.protocol.append(parent_route.protocol[0])
                parent_route.metric.append(match.group('metric').strip())
                parent_route.next_hop.append(match.group('next_hop').strip())
                parent_route.age.append(match.group('age').strip())
                try:
                    parent_route.interface.append(match.group('interface').strip())
                except IndexError:
                    parent_route.interface.append("N/A")
                break

    def get_host_range(self,subnet):
        try:
            range = ipaddress.ip_network(subnet)
            return range[1],range[-2]
        except ValueError:
            return "error", "error"
        except IndexError: # Handles /32
            return range[0], ""


    def generate_output_to_file(self):
        try:
            with open('routes.csv', 'w', newline='') as csv_file:
                spamwriter = csv.writer(
                    csv_file,
                    delimiter=',',
                    quotechar='|',
                    quoting=csv.QUOTE_MINIMAL
                )
                spamwriter.writerow([
                    'Route',
                    'Protocol',
                    'Metric',
                    'Next Hop',
                    'Age',
                    'Interface',
                    'From Range',
                    'To Range']
                )
                for entry in sorted(self.route_table):
                    route = self.get_route(entry)
                    first_ip, last_ip = self.get_host_range(route)
                    for no in range(len(route.protocol)):
                        spamwriter.writerow([
                            route.route,
                            route.protocol[no],
                            route.metric[no],
                            route.next_hop[no],
                            route.age[no],
                            route.interface[no],
                            first_ip,
                            last_ip
                        ])
            print ("  -- Output saved to 'routes.csv'")
        except:
            print ("  -- Unable to write to routes.csv, if the file is already open close it.")

    def read_file(self):
        start_processing = False
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
                    start_processing = True
                    continue
                if not start_processing:
                    continue

                line = line.strip().replace("\n","")
                #---------------------------------------
                # Define all the possible regex patterns
                #---------------------------------------
                # Line 1. BGP
                # Line 2. IGP (OSPF,EIGRP etc)
                # Line 3. Static routes
                # Line 4. Connected/local routes
                #---------------------------------------
                if start_processing:
                    patterns = [
                        r'(?P<protocol>[a-zA-Z] ..) (?P<route>.*) (?P<metric>.*) via (?P<next_hop>.*), ?(?P<age>.*), ?(?P<interface>.*)', \
                        r'(?P<protocol>[a-zA-Z]..) (?P<route>.*) (?P<metric>.*) via (?P<next_hop>.*), ?(?P<age>.*), ?(?P<interface>.*)', \
                        r'(?P<protocol>[a-zA-Z]) (?P<route>.*) is a summary, (?P<age>.*), (?P<interface>.*)', \
                        r'(?P<protocol>[a-zA-Z]..) (?P<route>.*) is a summary, (?P<age>.*), (?P<interface>.*)', \
                        r'(?P<protocol>B.*|B\*.*) (?P<route>.*) (?P<metric>.*) via (?P<next_hop>.*), (?P<age>.*)', \
                        r'(?P<protocol>S.*|S\*.*) (?P<route>.*) (?P<metric>.*) via (?P<next_hop>.*)', \
                        r'(?P<protocol>C.*|L.*) (?P<route>.*) is directly connected, (?P<interface>.*)'
                    ]
                    #-----------------------------------------------------
                    # Cycle through all the patterns and grab the matches
                    #-----------------------------------------------------
                    ecmp_route_found = False
                    for regex in patterns:
                        match = re.search(regex,line)
                        if match:
                            self.create_route(match)
                            prefix_being_processed = match.group('route').strip()
                            ecmp_route_found = True
                            break
                    if not ecmp_route_found:
                        self.add_ecmp_route(prefix_being_processed, line)

print ("Cisco IOS Route Parser version: '{}'".format(__version__))
c = Code()


