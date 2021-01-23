import numpy as np
from astropy.time import Time

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

print('checking structure...')


def structure_check(txt_content):
    dictionary_head = ['pobc_on', 'enable_saving_kpack', 'enable_saving_telemetry',
                       'enable_saving_status', 'star_tracker_on']
    dictionary_end = ['star_tracker_off', 'disable_saving_status',
                      'disable_saving_telemetry', 'disable_saving_kpack']
    head = txt_content[0:5]
    end = txt_content[-4:]

    for str in dictionary_head:
        n = 0
        for line in head:
            n += line.count(str)
            pass
        if n != 1:
            return False
        pass

    for str in dictionary_end:
        n = 0
        for line in end:
            n += line.count(str)
            pass
        if n != 1:
            return False

    for i in range(len(txt_content) - 1):
        time_index = 1
        if txt_content[i][time_index] == txt_content[i + 1][time_index]:
            return False

    return True


structure_bool = structure_check(txt_contents)
print(structure_bool)


def orbit_identification(txt_content):
    
    return 0

print(np.array(txt_contents))
