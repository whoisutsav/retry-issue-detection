import os


def dir_iterator(source_path):
    items=[]
    for subdir, dirs, files in list(os.walk(source_path))):
        for file in files:
            if not file.endswith(".java"):
                continue
    
            full_path = os.path.join(subdir, file)
            with open(full_path) as f:
                code=f.read()

            items.append((full_path,code))

    return items




