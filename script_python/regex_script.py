# Regular Expression
import re

# "remote_addr:0xc001,status:0,opcode:2"
txt = input("Insert command:\t")
regex = "^remote_addr:(0x)[a-fA-F0-9]{4}|[0-9]{0,2},status:[0,1],opcode:[1-3]"
x = re.search(regex, txt)

if x:
    print("YES! We have a match!")
else:
    print("No match")

