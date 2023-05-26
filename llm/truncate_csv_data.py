f = open("output_message.csv", "r")
lines=f.read().splitlines()
f2 = open("tmp_message.out", "w")
for line in lines:
    cols=line.split(";;;")
    if len(cols) < 6:
        print(line,file=f2)
        continue
    if len(cols[1]) > 1000:
        print(cols[0]+";;;"+cols[1][:1000]+";;;"+cols[2]+";;;"+cols[3]+";;;"+cols[4]+";;;"+cols[5],file=f2)
    else:
        print(line,file=f2)
    #if len(cols) < 2:
    #    continue
    #classification="?"
    #if cols[1].lower().startswith("yes"):
    #    classification="Y"
    #elif cols[1].lower().startswith("no"):
    #    classification="N"
    #print(cols[0]+";;;"+cols[1]+";;;"+classification,file=f2)
