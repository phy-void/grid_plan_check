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


def orbit_recognition(txt_content):
    power_on_time = []
    data_on_time = []
    data_off_time = []
    attitude_quaternion = []
    attitude_command_time = []

    power_on_index = []
    data_on_index = []
    data_off_index = []
    # judge attitude: through attitude_command_time
    sun_tracking_mode_index = []

    for line in txt_content:
        if line[2] == 'load_bin_file tg_PowerOnM.bin' or line[2] == 'load_bin_file tg_PowerOn.bin':
            power_on_time.append(line[1])
            power_on_index.append(txt_content.index(line))
        if line[2] == 'load_bin_file tg_TXDataOn.bin':
            data_on_time.append(line[1])
            line_index = txt_content.index(line)
            data_on_index.append(line_index)
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
            data_off_index.append(txt_content.index(line))
        if line[2] == 'magnetic_sun_tracking':
            magnetic_sun_tracking_index = txt_content.index(line)
        if line[2] == 'start_sun_tracking_mode':
            sun_tracking_mode_index.append(txt_content.index(line))

    if len(power_on_time) != len(data_on_time):  # first orbit has attitude command
        if Time(power_on_time[0], format='iso').unix - Time(data_off_time[0], format='iso').unix == 13 * 60 \
                and data_off_index[0] > data_on_index[0] and attitude_command_time[0] != None:
            data_on_time.pop(0)
            data_off_time.pop(0)
        else:
            return 'command sequence Error'
    else:
        attitude_quaternion.insert(0, [None, None, None])
        attitude_command_time.insert(0, None)
        pass

    # match attitude list and time list
    attitude_command_time.pop(-1)
    attitude_quaternion.pop(-1)

    # command sequence check
    for i in range(len(power_on_time)):
        error = 0
        att_n = 0
        if power_on_index[i] >= data_on_index[i] or data_on_index[i] >= data_off_index[i]:
            error += 1
        if magnetic_sun_tracking_index in range(data_on_index[-1], data_off_index[-1]):
            pass
        else:
            error += 1
        if attitude_command_time[i] != None and i < len(power_on_time) and attitude_command_time[i + 1] == None:
            if sun_tracking_mode_index[att_n] in range(data_on_index[i + 1], data_off_index[i + 1]):
                att_n += 1
            else:
                error += 1
    if error != 0:
        return 'command sequence Error'
    else:
        print('command sequence: True')

    return power_on_time, data_on_time, data_off_time, attitude_quaternion, attitude_command_time


def time_interval_check(power_on_time, data_off_time, attitude_command_time):
    total_orbit_number = len(power_on_time)
    power_on_time = Time(power_on_time, format='iso')
    data_off_time = Time(data_off_time, format='iso')
    for i in range(total_orbit_number - 1):
        if power_on_time[i + 1].unix - data_off_time[i].unix == 60:
            pass
        else:
            return 'time interval Error'
        if attitude_command_time[i] != None:
            attitude_command_time_1 = Time(attitude_command_time[i], format='iso')
            if power_on_time[i].unix - attitude_command_time_1.unix == 8 * 60:
                pass
            else:
                return 'time interval Error'

    return True


print('checking structure...')
structure_bool = structure_check(txt_contents)
# print(np.array(txt_contents))
print('structure: ', structure_bool)
print('checking orbit time sequence...')
# print(orbit_recognition(txt_contents))
power_on_time, data_on_time, data_off_time, attitude_quaternion, attitude_command_time = orbit_recognition(txt_contents)
time_sequence_bool = time_interval_check(power_on_time, data_off_time, attitude_command_time)
print('time interval: ', time_sequence_bool)
