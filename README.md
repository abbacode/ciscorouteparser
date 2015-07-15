# ciscorouteparser
Extracts Cisco route information from a local file and places it into .csv format (works for IOS and NXOS)

Instruction:
1. Copy the output of 'show ip route' from the device and save it as 'routes.txt'
2. Run the script



Example of what should be in the 'routes.txt' file, it should start at the point where you issue the command:

CiscoRouter#   show ip route     
Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area 
       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2
       E1 - OSPF external type 1, E2 - OSPF external type 2
       i - IS-IS, su - IS-IS summary, L1 - IS-IS level-1, L2 - IS-IS level-2
       ia - IS-IS inter area, * - candidate default, U - per-user static route
       o - ODR, P - periodic downloaded static route, H - NHRP, l - LISP
       + - replicated route, % - next hop override

Gateway of last resort is 10.68.4.2 to network 0.0.0.0

O*E1  0.0.0.0/0 [110/43] via 10.68.4.2, 1w3d, GigabitEthernet0/1
      10.0.0.0/8 is variably subnetted, 603 subnets, 17 masks
O E1     10.4.0.0/16 [110/171] via 10.68.4.2, 3d11h, GigabitEthernet0/1
O E1     10.4.1.0/24 [110/42] via 10.68.4.2, 1w3d, GigabitEthernet0/1
B    1.1.1.0/24 [200/0] via 1.1.1.1, 1d11h
                      [200/0] via 1.1.1.2, 1d12h
                      [200/0] via 1.1.1.3, 1d13h
B        10.4.4.0/24 [20/0] via 10.65.11.2, 7w0d
B        10.4.60.0/24 [20/0] via 10.65.11.2, 7w0d

Note. View this in raw format to see the proper output.
