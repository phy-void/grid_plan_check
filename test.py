import numpy as np
from astropy.time import Time

'''
a=[1,2,3]
print(a[-2:])
def f(a):
    if a[1]==2:
        return 0
    return 1
print(f(a))

'''
'''
a = '2021-01-20 02:03:00'
b = '2021-01-20 02:04:00'
time = [a, b]
time1 = Time(time, format='iso')
print((time1[1].unix-time1[0].unix)==60)
'''
'''
txt_file_path = './'
input_name = 'tg_20210120T01h00m30s.txt'
txt_file_name = txt_file_path + input_name
txt_file = open(txt_file_name, 'r')
txt_lines = txt_file.readlines()
txt_file.close()

txt_contents = []
command_index = 0
for i in range(len(txt_lines)):
    if i % 2 == 0:
        line = txt_lines[i].split(', ')
        line[-1] = line[-1].rstrip('\n')
        txt_contents.append(line)
    else:
        txt_contents[command_index].append(txt_lines[i].rstrip('\n'))
        command_index += 1
    pass

for line in txt_contents:
    if line[2] == 'load_bin_file tg_PowerOnM.bin' or line[2] == 'load_bin_file tg_PowerOn.bin':
        print(line[0])

print(txt_contents[5][2]== 'load_bin_file tg_PowerOnM.bin')
print(txt_contents[5][2].rstrip('\x00')=='load_bin_file tg_PowerOnM.bin')
print('load_bin_file tg_PowerOnM.bin'=='load_bin_file tg_PowerOnM.bin')
'''
a=[1,2,3]
a.pop(1)
print(a)