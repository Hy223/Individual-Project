import os

path = './speed_90'
files = os.listdir(path)
for file in files:
    file_name = file[:-4] + '.txt'
    with open(file_name, 'w') as f:
        f.write('2 0.5 0.5 0.999 0.999')