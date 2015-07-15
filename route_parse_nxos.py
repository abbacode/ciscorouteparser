import re
import csv
import ipaddress

__version__ = 1.0

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
            self.route_table[NewRoute.route] = NewRoute

    # Check the detail for the route and append it to the object
    def Add_Route_Detail(self,previous_route,line):
        route = self.Get_Route_Object(previous_route)

        route_patterns = [r'via (?P<next_hop>.*), (?P<interface>.*), (?P<metric>\[.*]), (?P<age>.*?), (?P<protocol>.*)', \
                         r'via (?P<next_hop>.*), (?P<metric>\[.*]), (?P<age>.*?), (?P<protocol>.*)']

        for pattern in route_patterns:
            match = re.search(pattern,line)
            if match:
                route.next_hop.append(match.group('next_hop').strip())
                route.metric.append(match.group('metric').strip())
                route.age.append(match.group('age').strip())
                route.protocol.append(match.group('protocol').strip().replace(",","_"))
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
        invalid_phrases = ["subnetted"]

        with open("routes.txt","r") as route_file:
            for line in route_file:
                #-----------------------
                # Ignore certain input
                #-----------------------
                if line.count(' ') < 2:
                    continue
                if any(x in line for x in invalid_phrases):
                    continue
                if "<string>" in line:
                    start_processing_routes = True
                    continue

                line = line.strip().replace("\n","")
                if start_processing_routes:
                    regex = r'(?P<route>[0-9].*), ubest/mbest: (?P<value>.*)'
                    match = re.search(regex,line)
                    if match:
                        self.Create_New_Route(match)
                        last_route = match.group('route').strip()
                        continue

                    self.Add_Route_Detail(last_route, line)


print ("Cisco NXOS Route Parser version: '{}'".format(__version__))
c = RouteParse()


