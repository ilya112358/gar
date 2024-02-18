# import csv
# import os

# file_paths = []
# for root, dirs, files in os.walk("Data"):
#     for file in files:
#         file_paths.append(file)
#         # f_name, f_ext = os.path.splitext(file)
#         # if f_ext == '.txt':
#         #     file_paths.append(f_name)
# file_paths.sort()
# filesL = [f for f in file_paths if f.startswith("L")]
# filesR = [f for f in file_paths if f.startswith("R")]
# filesOther = [f for f in file_paths if (f not in filesR) and (f not in filesL)]
# files_pairs = []
# for i in range(len(filesL)):
#     fL = filesL[i]
#     fR = filesR[i]
#     if fL.startswith("L_"):
#         section = fL[2:]
#     elif fL.startswith("Left "):
#         section = fL[5:]
#     if not fR.endswith(section):
#         print(f"Error! Check file names [{fL}] and [{fR}] for inconsistency")
#         exit(1)
#     files_set = (section[:-4], fL, fR)
#     files_pairs.append(files_set)
# files = files_pairs + filesOther
# print(files)

# # Open your CSV file in write mode
# with open("source.csv", "w", newline="") as file:
#     writer = csv.writer(file)

#     # Iterate over the list of tuples
#     for row in files:
#         # Write each tuple to the CSV file
#         writer.writerow(row)

# import csv
# import yaml

# data = []
# with open("source.csv", "r") as f:
#     reader = csv.reader(f)
#     for row in reader:
#         data.append({"name": row[0], "left_file": row[1], "right_file": row[2]})

# with open("config.yaml", "w") as f:
#     yaml.dump(data, f)

# import csv
# import toml

# data = []
# with open("source.csv", "r") as f:
#     reader = csv.reader(f)
#     for row in reader:
#         data.append({"name": row[0], "left_file": row[1], "right_file": row[2]})

# with open("config.toml", "w") as f:
#     toml.dump({"data": data}, f)

import toml

# Load the data from the TOML file
with open("config.toml", "r") as file:
    data = toml.load(file)

# Access the 'data' array
data_array = data["data"]

# Print each dictionary in the 'data' array
for item in data_array:
    print(item)
