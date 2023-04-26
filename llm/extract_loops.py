import subprocess

#format: file, start_line, end_line
LOOP_CSV = "hbase_loops_all.csv"
OUTPUT_DIR = "./loops/"
SOURCE_DIR = "hbase_e1ad781/"

with open("hbase_loops_all.csv", "r") as f:
    lines = f.readlines()
    for line in lines:
        cols = line.split(',')
        if len(cols) < 3:
            continue

        relative_path=cols[0][1:-1]
        source_file=SOURCE_DIR+relative_path
        start_line=int(cols[1])
        end_line=int(cols[2])
        output_file=OUTPUT_DIR+relative_path.replace(".", "_").replace("/","_")+"_"+str(start_line)+"_"+str(end_line)
        cmd = f"sed -n '{start_line},{end_line}p;{end_line+1}q' {source_file} > {output_file}"
        print(cmd)
        subprocess.run(cmd,shell=True)

        #print(cols[1])
        #print(cols[2])
        
