import os

input_dir = "//thescopefiles/projects/24028_BMW/shots/BMWi7Config01/publish/render"
exr_files = []

for dirpath, subdirs, files in os.walk(input_dir):
    for i in files:
        if i.endswith(".exr"):
            exr_files.append(os.path.join(dirpath, i))

print(exr_files)