from random import randint, choice
import sys

if sys.argv[1] == "1":
    print("!")
    print("!")
    for vlan in range(1, 4095):
        print(f"vlan {vlan}")
        print(f" name VLAN_{vlan}")
        print("!")
    print("!")
    for slot in range(1, 14):
        for port in range(1, 49):
            print(f"interface GigabitEthernet {slot}/{port}")
            # nosec will silence warnings about python random cryptographic inadequacy
            mode = choice(["trunk", "access"])  # nosec
            if mode == "trunk":
                print(" switchport")
                print(" switchport trunk encapsulation dot1q")
                print(" switchport mode trunk")
                # nosec will silence warnings about python random cryptographic inadequacy
                print(f" switchport trunk allowed vlan 1-{randint(2, 4094)}")  # nosec
                print(" switchport nonnegotiate")
                print(" spanning-tree guard root")
                print("!")
            elif mode == "access":
                print(" switchport")
                # nosec will silence warnings about python random cryptographic inadequacy
                print(f" switchport access vlan {randint(2, 4094)}")  # nosec
                print(" switchport mode access")
                print(" switchport nonnegotiate")
                print(" spanning-tree portfast")
                print("!")
    for vlan in range(1, 4095):
        print(f"interface Vlan {vlan}")
        print(" no shutdown")
        # nosec will silence warnings about python random cryptographic inadequacy
        mode = choice(["global", "vrf"])  # nosec
        if mode == "vrf":
            print(f"ip vrf forwarding VRF_{vlan}")
        print(f" description Layer3 SVI: vlan {vlan}")
        print(
            " ip address {}.{}.{}.0 255.255.255.0".format(
                randint(1, 224), randint(1, 255), randint(1, 255)  # nosec
            )
        )  # nosec
        print("!")

elif sys.argv[1] == "5":
    print("!")
    print("!")
    print("!")
    for acl_number in range(0, 100):
        print("ip access-list extended ACL_{}".format("%02i" % acl_number))
        # nosec will silence warnings about python random cryptographic inadequacy
        for ace in range(0, randint(20, 254)):  # nosec
            print(
                " permit {} any host 192.0.2.{}".format(
                    # nosec will silence warnings about python random cryptographic inadequacy
                    choice(["tcp", "udp", "ip"]),
                    ace,  # nosec
                )
            )
        print("!")
