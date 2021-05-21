import numpy as np
from astropy.time import Time
import re
from scipy import interpolate
from astropy.coordinates import get_sun
from astropy.coordinates import SkyCoord
from pyquaternion import Quaternion
import matplotlib.pyplot as plt
import struct

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


# given hex string and calculate 4 byte CRC
def calc_crc(hex_str):
    crc_tab = np.array([
        0x00000000, 0xF26B8303, 0xE13B70F7, 0x1350F3F4, 0xC79A971F, 0x35F1141C, 0x26A1E7E8, 0xD4CA64EB,
        0x8AD958CF, 0x78B2DBCC, 0x6BE22838, 0x9989AB3B, 0x4D43CFD0, 0xBF284CD3, 0xAC78BF27, 0x5E133C24,
        0x105EC76F, 0xE235446C, 0xF165B798, 0x030E349B, 0xD7C45070, 0x25AFD373, 0x36FF2087, 0xC494A384,
        0x9A879FA0, 0x68EC1CA3, 0x7BBCEF57, 0x89D76C54, 0x5D1D08BF, 0xAF768BBC, 0xBC267848, 0x4E4DFB4B,
        0x20BD8EDE, 0xD2D60DDD, 0xC186FE29, 0x33ED7D2A, 0xE72719C1, 0x154C9AC2, 0x061C6936, 0xF477EA35,
        0xAA64D611, 0x580F5512, 0x4B5FA6E6, 0xB93425E5, 0x6DFE410E, 0x9F95C20D, 0x8CC531F9, 0x7EAEB2FA,
        0x30E349B1, 0xC288CAB2, 0xD1D83946, 0x23B3BA45, 0xF779DEAE, 0x05125DAD, 0x1642AE59, 0xE4292D5A,
        0xBA3A117E, 0x4851927D, 0x5B016189, 0xA96AE28A, 0x7DA08661, 0x8FCB0562, 0x9C9BF696, 0x6EF07595,
        0x417B1DBC, 0xB3109EBF, 0xA0406D4B, 0x522BEE48, 0x86E18AA3, 0x748A09A0, 0x67DAFA54, 0x95B17957,
        0xCBA24573, 0x39C9C670, 0x2A993584, 0xD8F2B687, 0x0C38D26C, 0xFE53516F, 0xED03A29B, 0x1F682198,
        0x5125DAD3, 0xA34E59D0, 0xB01EAA24, 0x42752927, 0x96BF4DCC, 0x64D4CECF, 0x77843D3B, 0x85EFBE38,
        0xDBFC821C, 0x2997011F, 0x3AC7F2EB, 0xC8AC71E8, 0x1C661503, 0xEE0D9600, 0xFD5D65F4, 0x0F36E6F7,
        0x61C69362, 0x93AD1061, 0x80FDE395, 0x72966096, 0xA65C047D, 0x5437877E, 0x4767748A, 0xB50CF789,
        0xEB1FCBAD, 0x197448AE, 0x0A24BB5A, 0xF84F3859, 0x2C855CB2, 0xDEEEDFB1, 0xCDBE2C45, 0x3FD5AF46,
        0x7198540D, 0x83F3D70E, 0x90A324FA, 0x62C8A7F9, 0xB602C312, 0x44694011, 0x5739B3E5, 0xA55230E6,
        0xFB410CC2, 0x092A8FC1, 0x1A7A7C35, 0xE811FF36, 0x3CDB9BDD, 0xCEB018DE, 0xDDE0EB2A, 0x2F8B6829,
        0x82F63B78, 0x709DB87B, 0x63CD4B8F, 0x91A6C88C, 0x456CAC67, 0xB7072F64, 0xA457DC90, 0x563C5F93,
        0x082F63B7, 0xFA44E0B4, 0xE9141340, 0x1B7F9043, 0xCFB5F4A8, 0x3DDE77AB, 0x2E8E845F, 0xDCE5075C,
        0x92A8FC17, 0x60C37F14, 0x73938CE0, 0x81F80FE3, 0x55326B08, 0xA759E80B, 0xB4091BFF, 0x466298FC,
        0x1871A4D8, 0xEA1A27DB, 0xF94AD42F, 0x0B21572C, 0xDFEB33C7, 0x2D80B0C4, 0x3ED04330, 0xCCBBC033,
        0xA24BB5A6, 0x502036A5, 0x4370C551, 0xB11B4652, 0x65D122B9, 0x97BAA1BA, 0x84EA524E, 0x7681D14D,
        0x2892ED69, 0xDAF96E6A, 0xC9A99D9E, 0x3BC21E9D, 0xEF087A76, 0x1D63F975, 0x0E330A81, 0xFC588982,
        0xB21572C9, 0x407EF1CA, 0x532E023E, 0xA145813D, 0x758FE5D6, 0x87E466D5, 0x94B49521, 0x66DF1622,
        0x38CC2A06, 0xCAA7A905, 0xD9F75AF1, 0x2B9CD9F2, 0xFF56BD19, 0x0D3D3E1A, 0x1E6DCDEE, 0xEC064EED,
        0xC38D26C4, 0x31E6A5C7, 0x22B65633, 0xD0DDD530, 0x0417B1DB, 0xF67C32D8, 0xE52CC12C, 0x1747422F,
        0x49547E0B, 0xBB3FFD08, 0xA86F0EFC, 0x5A048DFF, 0x8ECEE914, 0x7CA56A17, 0x6FF599E3, 0x9D9E1AE0,
        0xD3D3E1AB, 0x21B862A8, 0x32E8915C, 0xC083125F, 0x144976B4, 0xE622F5B7, 0xF5720643, 0x07198540,
        0x590AB964, 0xAB613A67, 0xB831C993, 0x4A5A4A90, 0x9E902E7B, 0x6CFBAD78, 0x7FAB5E8C, 0x8DC0DD8F,
        0xE330A81A, 0x115B2B19, 0x020BD8ED, 0xF0605BEE, 0x24AA3F05, 0xD6C1BC06, 0xC5914FF2, 0x37FACCF1,
        0x69E9F0D5, 0x9B8273D6, 0x88D28022, 0x7AB90321, 0xAE7367CA, 0x5C18E4C9, 0x4F48173D, 0xBD23943E,
        0xF36E6F75, 0x0105EC76, 0x12551F82, 0xE03E9C81, 0x34F4F86A, 0xC69F7B69, 0xD5CF889D, 0x27A40B9E,
        0x79B737BA, 0x8BDCB4B9, 0x988C474D, 0x6AE7C44E, 0xBE2DA0A5, 0x4C4623A6, 0x5F16D052, 0xAD7D5351
    ])

    crc = 0xFFFFFFFF

    n = len(hex_str)
    if n == 0:
        return crc

    for i in range(0, n, 2):
        byte = hex_str[i:i + 2]
        crc = crc_tab[(crc ^ int('0x' + byte, 0)) & 0xFF] ^ (crc >> 8)  # modified python3

    crc_hex = str("%08x" % (crc ^ 0xFFFFFFFF))
    return crc_hex


def hex_command_check(txt_file_name):
    cmd_list = {
        'magnetic_sun_tracking': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 7e 34 00 14 00 00 00 00 00 08 00 00 00 00 34 08 aa aa b9 16 42 17',
        #
        'enable_saving_kpack': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 01 02 00 14 00 00 00 00 00 0e 00 00 00 00 03 02 00 0a ff ff ff ff ff ff 19 e6 26 1a',
        #
        'disable_saving_kpack': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 01 02 00 14 00 00 00 00 00 0e 00 00 00 00 04 02 00 00 00 00 ff ff ff ff ed 65 4d df',
        #
        'enable_saving_telemetry': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 01 02 00 14 00 00 00 00 00 0e 00 00 00 00 03 34 00 01 ff ff ff ff ff ff 43 8c 02 22',
        #
        'disable_saving_telemetry': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 01 02 00 14 00 00 00 00 00 0e 00 00 00 00 04 34 00 00 00 00 ff ff ff ff 41 27 e1 ec',
        #
        'enable_saving_status': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 01 02 00 14 00 00 00 00 00 0e 00 00 00 00 03 00 00 01 ff ff ff ff ff ff 02 5f 74 70',
        #
        'star_tracker_on': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 01 00 00 14 00 00 00 00 00 07 00 00 00 00 03 1f aa 71 6d 7e ca',
        'star_tracker_off': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 01 00 00 14 00 00 00 00 00 07 00 00 00 00 03 1f 00 b8 c4 e3 54',
        'disable_saving_status': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 01 02 00 14 00 00 00 00 00 0e 00 00 00 00 04 00 00 00 00 00 ff ff ff ff 00 f4 97 be',
        #
        'upload_quaternion': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 7e 37 00 14 00 00 00 00 00 11 00 00 00 00 08',
        #
        'set_inertial_pointing_mode': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 7e 33 00 14 00 00 00 00 00 08 00 00 00 00 33 29 00 aa 40 58 1a 76',
        #
        'start_inertial_pointing': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 7e 34 00 14 00 00 00 00 00 08 00 00 00 00 34 07 aa aa f5 b7 18 bb',
        #
        'load_bin_file': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 01 00 00 14 00 02 00 00 00 15 00 00 00 00 04',  #
        'start_sun_tracking_mode': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 7e 34 00 14 00 00 00 00 00 08 00 00 00 00 34 04 aa aa 1f 99 d8 c8',
        #
        'pobc_on': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 01 00 00 14 00 00 00 00 00 07 00 00 00 00 03 00 aa a9 d1 85 b6',
        'reboot_pobc': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 01 c2 00 05 00 00 00 00 00 14 00 00 00 00 70 72 65 73 74 2e 62 69 6e 00 00 00 00 00 00 00',
        'clear_flash': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 01 c2 00 05 00 00 00 00 00 14 00 00 00 00 74 79 5f 70 6c 5f 65 66 2e 62 69 6e 00 00 00 00',
        'gyro_lowpassfilter_on': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 7e 33 00 05 00 00 00 00 00 08 00 00 00 00 33 18 01 aa',
        'gyro_lowpassfilter_off': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 7e 33 00 05 00 00 00 00 00 08 00 00 00 00 33 18 00 aa',
        'enable_pi_control': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 7e 34 00 05 00 00 00 00 00 08 00 00 00 00 34 1e 01 aa',
        'disable_pi_control': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 7e 34 00 05 00 00 00 00 00 08 00 00 00 00 34 1e 00 aa',
        'enable_mwheel_unload': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 7e 34 00 05 00 00 00 00 00 08 00 00 00 00 34 20 01 aa',
        'disable_mwheel_unload': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 7e 34 00 05 00 00 00 00 00 08 00 00 00 00 34 20 00 aa',
        'temp1': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 7e 36 00 05 00 00 00 00 00 08 00 00 00 00 36 01 25 aa',
        'temp2': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 7e 36 00 05 00 00 00 00 00 08 00 00 00 00 36 02 1b aa',
        'temp3': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 7e 36 00 05 00 00 00 00 00 08 00 00 00 00 36 01 00 aa',
        'temp4': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 7e 36 00 05 00 00 00 00 00 08 00 00 00 00 36 02 00 aa',
        'disable_auto_tg_read': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 11 03 00 05 00 00 00 00 00 0c 00 00 00 00 05 06 00 00 00 00 00 00',
        'adjust_reading_speed_1': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 11 03 00 05 00 00 00 00 00 0c 00 00 00 00 05 54 01 00 00 00 00 00',
        'adjust_reading_speed_2': 'eb 90 01 00 01 01 00 00 00 00 00 00 01 00 11 03 00 05 00 00 00 00 00 0c 00 00 00 00 05 52 01 00 00 00 00 00'
    }

    # since the'\x00' hex symbol after some commands like 'tg_PowerOn.bin' may cause difference between main function and this part,
    # this function is made to check the hex code and read txt file independently.
    txt_file = open(txt_file_name, 'r')
    txt_lines = txt_file.readlines()
    txt_file.close()

    txt_contents = []
    command_index = 0
    for i in range(len(txt_lines)):
        if i % 2 == 0:
            line = txt_lines[i].split(', ')
            line[-1] = line[-1].rstrip('\n')
            #        line[-1] = line[-1].rstrip('\x00')
            txt_contents.append(line)
        else:
            txt_contents[command_index].append(txt_lines[i].rstrip('\n'))
            command_index += 1
        pass

    error_index = 0
    for i in range(len(txt_contents)):
        txt_contents[i][3] = txt_contents[i][3].replace(' ', '')
        if txt_contents[i][2].startswith('load_bin_file'):
            file_name = txt_contents[i][2].split(" ")[1]
            cmd = cmd_list['load_bin_file'].replace(' ', '') + file_name.encode('utf-8').hex()
            cmd += calc_crc(cmd)
            if (txt_contents[i][3][8:] != cmd):
                error_index = i + 1
                break
            pass
        elif txt_contents[i][2].startswith('upload_quaternion'):
            q = txt_contents[i][2].split(" ")[1:]
            qhex1 = struct.unpack('>f', bytes.fromhex(txt_contents[i][3][-32:-24]))[0]
            qhex2 = struct.unpack('>f', bytes.fromhex(txt_contents[i][3][-24:-16]))[0]
            qhex3 = struct.unpack('>f', bytes.fromhex(txt_contents[i][3][-16:-8]))[0]
            if abs(float(q[0]) - qhex1) >= 2E-6:
                error_index = i + 1
                break
            if abs(float(q[1]) - qhex2) >= 2E-6:
                error_index = i + 1
                break
            if abs(float(q[2]) - qhex3) >= 2E-6:
                error_index = i + 1
                break
        else:
            if (cmd_list[txt_contents[i][2]].replace(' ', '') != txt_contents[i][3][8:]):
                error_index = i + 1
                break

    '''
    if (error_index != 0):
        print("the cmd_code in line #%d is wrong!" % error_index)
        exit()
        '''

    for line in txt_contents:
        time = Time(line[1], format='iso').unix - Time(txt_contents[0][1], format='iso').unix
        cmd_time = int(line[3][:8], 16)
        if (time != cmd_time):
            error_index = i + 1
            break

    '''
    if (error_index != 0):
        print("the cmd_code in line #%d is wrong!" % error_index)
        '''

    return error_index


error_index = hex_command_check(txt_file_name)
print('checking command code in hex form...')
if error_index != 0:
    print("the cmd_code in line #%d is wrong!" % error_index)
    pass
else:
    print('hex code: True')

print('checking structure...')
structure_bool = structure_check(txt_contents)
# print(np.array(txt_contents))
print('structure: ', structure_bool)
print('checking orbit time sequence...')
# print(orbit_recognition(txt_contents))

power_on_time, data_on_time, data_off_time, attitude_quaternion, attitude_command_time = orbit_recognition(txt_contents)
# print(len(power_on_time), np.shape(attitude_quaternion), len(data_on_time))
# print(attitude_command_time)
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
