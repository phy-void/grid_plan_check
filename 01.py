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
        line[-1] = line[-1].rstrip('\x00')  # ???
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
    # check repeated time
    for i in range(len(txt_content) - 1):
        time_index = 1
        if txt_content[i][time_index] == txt_content[i + 1][time_index]:
            return False

    return True


structure_bool = structure_check(txt_contents)
print('structure: ', structure_bool)
print('checking orbit time sequence...')

def orbit_recognition(txt_content):
    power_on_time = []
    data_on_time = []
    data_off_time = []
    attitude_quaternion = []
    attitude_command_time = []
    for line in txt_content:
        if line[2] == 'load_bin_file tg_PowerOnM.bin' or line[2] == 'load_bin_file tg_PowerOn.bin':
            power_on_time.append(line[1])
        if line[2] == 'load_bin_file tg_TXDataOn.bin':
            data_on_time.append(line[1])
            line_index = txt_content.index(line)
            next_line = txt_content[line_index + 1][2].split(' ')
            if next_line[0] == 'upload_quaternion':
                attitude_quaternion.append([float(next_line[1]), float(next_line[2]), float(next_line[3])])
                # check attitude command structure
                if txt_content[line_index + 2][2] == 'set_inertial_pointing_mode' \
                        and txt_content[line_index + 3][2] == 'start_inertial_pointing':
                    attitude_command_time.append(txt_content[line_index + 3][1])
                else:
                    return 'attitude command structure Error'
            else:
                attitude_quaternion.append([None, None, None])
                attitude_command_time.append(None)
        if line[2] == 'load_bin_file tg_TXDataOff.bin':
            data_off_time.append(line[1])

    return power_on_time, data_on_time, data_off_time, attitude_quaternion, attitude_command_time


power_on_time, data_on_time, data_off_time, attitude_quaternion, \
attitude_command_time = orbit_recognition(txt_contents)


def time_interval_check(power_on_time, data_off_time, attitude_command_time):
    total_orbit_number1 = len(power_on_time)

    power_on_time = Time(power_on_time, format='iso')
    data_off_time = Time(data_off_time, format='iso')
    for i in range(total_orbit_number1 - 1):
        if power_on_time[i + 1].unix - data_off_time[i].unix == 60:
            pass
        else:
            return 'time interval Error'
        if attitude_command_time[i] != None:
            attitude_command_time_1 = Time(attitude_command_time[i], format='iso')
            if power_on_time[i + 1].unix - attitude_command_time_1.unix == 8 * 60:
                pass
            else:
                return 'time interval Error'

    return True


# print(np.array(txt_contents))

time_sequence_bool = time_interval_check(power_on_time, data_off_time, attitude_command_time)
print('time sequence: ', time_sequence_bool)
