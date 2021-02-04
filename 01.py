import numpy as np
from astropy.time import Time
import re
from scipy import interpolate
from astropy.coordinates import get_sun
from astropy.coordinates import SkyCoord
from pyquaternion import Quaternion
import matplotlib.pyplot as plt

np.set_printoptions(precision=2, threshold=100)

txt_file_path = './command txt file/'
input_name = 'tg_20210128T15h00m30s.txt'
# tg_20210119T15h00m30s.txt tg_20210120T01h00m30s.txt tg_20210128T01h00m30s.txt(use for test)
txt_file_name = txt_file_path + input_name
orbit_file_path = 'orb_20210128.txt'
saa_coord_file = 'coords.txt'
saa_flux_file = 'AE8_MIN_0.1MeV.txt'

txt_file = open(txt_file_name, 'r')
txt_lines = txt_file.readlines()
txt_file.close()

# read txt file:
# data format: list; element: ['#01', '2021-01-28 01:00:30', 'pobc_on', '(hex-command)']
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


# the first five commands and the last four are fixed
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
    # check repeated time: commands should be arranged by time sequence
    for i in range(len(txt_content) - 1):
        time_index = 1
        if txt_content[i][time_index] >= txt_content[i + 1][time_index]:
            return False

    return True


# recognize each orbit time from txt_contents
def orbit_recognition(txt_content):
    power_on_time = []
    data_on_time = []
    data_off_time = []
    attitude_quaternion = []
    attitude_command_time = []

    # these index lists are used for checking command existence and sequence
    power_on_index = []
    data_on_index = []
    data_off_index = []
    # judge attitude: through attitude_command_time
    sun_tracking_mode_index = []

    for line in txt_content:
        # the first start in a day will use PowerOnM, to examine some electronic status
        if line[2] == 'load_bin_file tg_PowerOnM.bin' or line[2] == 'load_bin_file tg_PowerOn.bin':
            if line[2] == 'load_bin_file tg_PowerOnM.bin':
                PowerOnM = True
            else:
                PowerOnM = False
            power_on_time.append(line[1])
            power_on_index.append(txt_content.index(line))
        if line[2] == 'load_bin_file tg_TXDataOn.bin':
            data_on_time.append(line[1])
            try:
                if attitude_command_time[-1] == None:
                    line_index = txt_content.index(line)
                else:
                    line_index = txt_content.index(line) + 1
            except:
                line_index = txt_content.index(line)
            data_on_index.append(line_index)
            next_line = txt_content[line_index + 1][2].split(' ')
            if next_line[0] == 'upload_quaternion':  # these three commands suggest attitude control
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

    for i in range(len(txt_content)):
        if 'upload_quaternion' in txt_content[i][2]:
            first_attitude_index = i
            break

    if first_attitude_index < power_on_index[0]:  # first orbit has attitude command
        if (Time(power_on_time[0], format='iso').unix - Time(txt_content[first_attitude_index + 2][1],
                                                             format='iso').unix == 8 * 60 and PowerOnM == False) \
                or (Time(power_on_time[0], format='iso').unix - Time(txt_content[first_attitude_index + 2][1],
                                                                     format='iso').unix == 13 * 60 and PowerOnM == True) \
                and txt_content[first_attitude_index + 1][2] == 'set_inertial_pointing_mode' \
                and txt_content[first_attitude_index + 2][2] == 'start_inertial_pointing':
            first_quaternion = txt_content[first_attitude_index][2].split(' ')
            attitude_quaternion.insert(0, [float(first_quaternion[1]), float(first_quaternion[2]),
                                           float(first_quaternion[3])])
            attitude_command_time.insert(0, txt_content[first_attitude_index + 2][1])
        else:
            print(1)  # ...
            return 'command sequence Error'
    else:
        attitude_quaternion.insert(0, [None, None, None])
        attitude_command_time.insert(0, None)
        pass

    # match attitude list and time list
    attitude_command_time.pop(-1)
    attitude_quaternion.pop(-1)

    # command sequence check
    error = 0
    att_n = 0
    for i in range(len(power_on_time)):
        # sequence in each orbit: power_on->data_on->data_off
        if power_on_index[i] >= data_on_index[i] or data_on_index[i] >= data_off_index[i]:
            error += 1
        # the last data transfer: set satellite to magnetic_sun_tracking mode
        if magnetic_sun_tracking_index in range(data_on_index[-1], data_off_index[-1]):
            pass
        else:
            error += 1
        # if an orbit after one with attitude, should transfer 'start_sun_tracking_mode' before it
        if attitude_command_time[i] != None and i < len(power_on_time) - 1:
            if sun_tracking_mode_index[att_n] in range(data_on_index[i], data_off_index[i]):
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
        if attitude_command_time[i] != None and i != 0:
            attitude_command_time_1 = Time(attitude_command_time[i], format='iso')
            if power_on_time[i].unix - attitude_command_time_1.unix == 8 * 60:
                pass
            else:
                return 'time interval Error'

    return True


def read_STK_orbit_file(filename):
    print('Loading STK orbit file {}...'.format(filename))
    with open(filename) as f:
        # to remove \r\n using the following line
        lines = [line.rstrip() for line in f]

    # headers ends to ----
    q = [l.startswith('---') for l in lines]
    qdash = np.where(q)[0][0]
    sdata = lines[qdash + 1:]  # skip xxx lines of the file header

    # find out the start and end positions of each column
    ld = lines[qdash]
    i0 = [i.start() + 1 for i in re.finditer(' -', ld)]
    i1 = [i.start() for i in re.finditer('- ', ld)]
    i0.insert(0, 0)
    i1.append(len(ld) - 1)

    n_row = len(sdata)
    n_col = len(i0)

    smon = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
            'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}

    t_bj_str = []
    data = np.empty([n_row, n_col - 1])
    for i in range(n_row):
        s = sdata[i]

        # get the time string, like 13 Jan 2019 00:00:00.000
        t = s[i0[0]: i1[0] + 1]
        # there are two kinds of length of the format of time string 3 Jan 2019 00:00:00.000 or 13 Jan 2019 00:00:00.000
        if t[1] == ' ':  # like 3 Jan 2019 00:00:00.000
            str_isot = t[6:10] + '-' + smon[t[2:5]] + '-' + t[0:1].strip() + 'T' + t[11:23]
        else:  # like 13 Jan 2019 00:00:00.000
            str_isot = t[7:11] + '-' + smon[t[3:6]] + '-' + t[0:2].strip() + 'T' + t[12:24]
        t_bj_str.append(str_isot)

        for j in range(1, n_col):
            data[i, j - 1] = np.float(s[i0[j]: i1[j] + 1])

    # get the names of the columns
    lname = lines[qdash - 1]
    names = [lname[i0[j]:i1[j] + 1] for j in range(n_col)]

    j = np.where(['Latitude' in x for x in names])[0][0] - 1
    lat = np.deg2rad(data[:, j])
    j = np.where(['Longitude' in x for x in names])[0][0] - 1
    lon = np.deg2rad(data[:, j])
    j = np.where(['Altitude' in x for x in names])[0][0] - 1
    alt = data[:, j]
    j = np.where(['RightAscension' in x for x in names])[0][0] - 1
    ra = np.deg2rad(data[:, j])
    j = np.where(['Declination' in x for x in names])[0][0] - 1
    dec = np.deg2rad(data[:, j])

    # Beijing Time
    t_bj = Time(t_bj_str, format='isot')
    return t_bj, lat, lon, alt, ra, dec


def find_orbit_time_index(orb_time, power_on_time, data_on_time):
    # orb_time: Time; power_on_time, data_on_time: list
    total_orbit_number = len(power_on_time)
    orbit_time_len = len(orb_time)
    power_on_time = Time(power_on_time, format='iso')
    data_on_time = Time(data_on_time, format='iso')
    power_on_time_index = []
    data_on_time_index = []
    for i in range(total_orbit_number):
        for j in range(orbit_time_len):
            if power_on_time[i].unix <= orb_time[j].unix:
                power_on_time_index.append(j)
                break
        for j in range(orbit_time_len):
            if data_on_time[i].unix <= orb_time[j].unix:
                data_on_time_index.append(j)
                break

    for j in range(orbit_time_len):
        if power_on_time[0].unix - 5 * 60 <= orb_time[j].unix:
            first_power_on_index = j
    return power_on_time_index, data_on_time_index, first_power_on_index


def SAA_check(power_on_time_index, data_on_time_index, orb_log_flux, first_power_on_index):
    total_orbit_number = len(power_on_time_index)
    for i in range(total_orbit_number):
        for j in range(power_on_time_index[i], data_on_time_index[i]):
            if orb_log_flux[j] >= 1.0:
                return False
    for i in range(first_power_on_index, power_on_time_index[0]):
        if orb_log_flux[i] >= 1.0:
            return False
    return True


def calculate_quaternion(attitude_quaternion):
    q_list = []
    for i in attitude_quaternion:
        if i[0] == None:
            pass
        else:
            q_234 = np.array(i)
            sum = np.sum(np.power(q_234, 2))
            q_1 = np.sqrt(1 - sum)
            q = Quaternion(q_1, q_234[0], q_234[1], q_234[2])
            q_list.append(q)

    return q_list


def vector_angle(v1, v2):
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    cos = np.inner(v1, v2) / (n1 * n2)
    return np.arccos(cos)


def radec_to_xyz(ra, dec):
    x = np.cos(dec) * np.cos(ra)
    y = np.cos(dec) * np.sin(ra)
    z = np.sin(dec)
    length = np.shape(x)
    if len(length) == 0:
        length = 1
    else:
        length = length[0]
    x = np.reshape(x, [length, 1])
    y = np.reshape(y, [length, 1])
    z = np.reshape(z, [length, 1])
    xyz = np.concatenate((x, y, z), axis=1)
    return xyz


def pointing_check(target_ra, target_dec, q_list):
    target_xyz = radec_to_xyz(target_ra, target_dec)[0]
    detector_initial = np.array([0, 0, -1])
    angle = []
    error = 0
    for q in q_list:
        detector_xyz = q.rotate(detector_initial)
        angle1 = np.rad2deg(vector_angle(target_xyz, detector_xyz))
        angle.append(angle1)
        if angle1 >= 15:
            error += 1
    print('angle between target and detector: ', angle)
    if error > 0:
        return False, angle
    else:
        return True, angle


def index_select(power_on_time_index, data_on_time_index, attitude_command_time, orbit_len):
    index = np.array(range(orbit_len))
    index_bool = (index > -1)
    att_index_bool = (index > -1)
    index_bool_list = []
    att_index_bool_list = []
    for i in range(len(power_on_time_index)):
        index_bool_list.append(index_bool & (index >= power_on_time_index[i]) & (index < data_on_time_index[i]))
        if attitude_command_time[i] is not None:
            att_index_bool_list.append(
                att_index_bool & (index >= power_on_time_index[i]) & (index < data_on_time_index[i]))
    return index_bool_list, att_index_bool_list


def star_tracker_angle_check(st_xyz, q_list, earth_ra, earth_dec, c_sun, att_index_bool_list):
    earth_xyz = radec_to_xyz(earth_ra, earth_dec)
    sun_xyz = radec_to_xyz(c_sun.ra.radian, c_sun.dec.radian)
    st_xyz_r = []
    st_earth_angle = []
    st_sun_angle = []
    for q in q_list:
        st_xyz_r1 = q.rotate(st_xyz)
        st_xyz_r.append(st_xyz_r1)
    for i in range(len(att_index_bool_list)):
        sun_xyz1 = sun_xyz[att_index_bool_list[i]]
        earth_xyz1 = earth_xyz[att_index_bool_list[i]]
        for j in range(len(sun_xyz1)):
            angle_s = vector_angle(sun_xyz1[j], st_xyz_r[i])
            angle_e = vector_angle(earth_xyz1[j], st_xyz_r[i])
            st_earth_angle.append(angle_e)
            st_sun_angle.append(angle_s)
            if np.rad2deg(angle_e) < 100 or np.rad2deg(angle_s) < 60:
                return False
    st_earth_angle = np.array(st_earth_angle)
    st_sun_angle = np.array(st_sun_angle)
    print('angle between sun and star tracker: ', np.rad2deg(st_sun_angle))
    print('angle between earth and star tracker: ', np.rad2deg(st_earth_angle))
    return True


print('checking structure...')
structure_bool = structure_check(txt_contents)
# print(np.array(txt_contents))
print('structure: ', structure_bool)
print('checking orbit time sequence...')
# print(orbit_recognition(txt_contents))

power_on_time, data_on_time, data_off_time, attitude_quaternion, attitude_command_time = orbit_recognition(txt_contents)
# print(len(power_on_time), np.shape(attitude_quaternion), len(data_on_time))
print(attitude_command_time)
time_sequence_bool = time_interval_check(power_on_time, data_off_time, attitude_command_time)
print('time interval: ', time_sequence_bool)

orb_time_bj, orb_lat, orb_lon, orb_alt, orb_ra, orb_dec, = read_STK_orbit_file(orbit_file_path)
orbit_len = len(orb_ra)

coord = np.loadtxt(saa_coord_file, comments="'", skiprows=26, delimiter=',')
map_lat = np.deg2rad(coord[:, 1])
map_lon = np.deg2rad(coord[:, 2])

flux = np.loadtxt(saa_flux_file, comments="'", skiprows=30, delimiter=',')[:, 2]
flux[flux <= 0] = 1e-100

saa_n_lon = 121  # for interpolate
saa_n_lat = 90
# get the flux along the trajectory
points = np.zeros([saa_n_lat * saa_n_lon, 2])
points[:, 0] = map_lon
points[:, 1] = map_lat
orb_log_flux = interpolate.griddata(points, np.log10(flux), (orb_lon, orb_lat), method='linear')

power_on_time_index, data_on_time_index, first_power_on_index = find_orbit_time_index(orb_time_bj, power_on_time,
                                                                                      data_on_time)
print('checking orbit flux...')
print('flux check: ', SAA_check(power_on_time_index, data_on_time_index, orb_log_flux, first_power_on_index))

# calculate detector pointing: -z rotate by quaternion
# NOTE: after 'upload_quaternion' there are three numbers, which are the 2, 3, 4th parameter of Quaternion(). The first parameter is Sqrt[1-a^2-b^2-c^2].
q_list = calculate_quaternion(attitude_quaternion)
target_ra = np.deg2rad(083.63308)
target_dec = np.deg2rad(22.01450)
pointing_bool, det_target_angle = pointing_check(target_ra, target_dec, q_list)
print('checking satellite attitude...')
print('detector pointing check: ', pointing_bool)

on_index_bool_list, att_index_bool_list = index_select(power_on_time_index, data_on_time_index, attitude_command_time,
                                                       orbit_len)

earth_ra = orb_ra + np.pi
earth_dec = -orb_dec
sun_pos = get_sun(orb_time_bj)
sun_ra = sun_pos.ra.radian
sun_dec = sun_pos.dec.radian
c_sun = SkyCoord(ra=sun_ra, dec=sun_dec, unit='radian', frame='fk5')

detector_xyz = np.array([0, 0, -1])
solar_panel_xyz = np.array([0, -1, 0])
star_tracker_xyz = -np.sin(np.deg2rad(18)) * solar_panel_xyz + np.cos(np.deg2rad(18)) * detector_xyz

star_tracker_bool = star_tracker_angle_check(star_tracker_xyz, q_list, earth_ra, earth_dec, c_sun, att_index_bool_list)
print('star tracker angle check: ', star_tracker_bool)

# pyplot
plt.figure(figsize=[9, 6])
ttt = flux > 1
plt.scatter(np.rad2deg(map_lon[ttt]), np.rad2deg(map_lat[ttt]), s=1)

for i in range(len(attitude_command_time)):
    if attitude_command_time[i] is not None:
        plt.scatter(np.rad2deg(orb_lon[on_index_bool_list[i]]), np.rad2deg(orb_lat[on_index_bool_list[i]]),
                    c='r', s=1)
    else:
        plt.scatter(np.rad2deg(orb_lon[on_index_bool_list[i]]), np.rad2deg(orb_lat[on_index_bool_list[i]]),
                    c='m', s=1)

plt.xlabel('longitude')
plt.ylabel('latitude')
plt.show()
