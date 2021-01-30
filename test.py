import numpy as np
from astropy.time import Time
import re
from scipy import interpolate
from pyquaternion import Quaternion

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

'''def read_STK_orbit_file(filename):
    print("   Loading STK orbit file %s" % (filename))
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


orbit_file_path = 'orb_20201118.txt'
orb_time_bj, orb_lat, orb_lon, orb_alt, orb_ra, orb_dec, = read_STK_orbit_file(orbit_file_path)
print(orb_time_bj)
print(orb_alt)
print(orb_ra)

saa_coord_file = 'coords.txt'
saa_flux_file = 'AE8_MIN_0.1MeV.txt'

coord = np.loadtxt(saa_coord_file, comments="'", skiprows=26, delimiter=',')
map_lat = np.deg2rad(coord[:, 1])
map_lon = np.deg2rad(coord[:, 2])

flux = np.loadtxt(saa_flux_file, comments="'", skiprows=30, delimiter=',')[:, 2]
flux[flux <= 0] = 1e-100

saa_n_lon = 121 #for interpolate
saa_n_lat = 90
# get the flux along the trajectory
points = np.zeros([saa_n_lat * saa_n_lon, 2])
points[:, 0] = map_lon
points[:, 1] = map_lat
orb_log_flux = interpolate.griddata(points, np.log10(flux), (orb_lon, orb_lat), method='linear')

print(len(orb_time_bj))
print(len(orb_log_flux))
'''
'''print(('a' in 'abc d'))
'''
'''if 10 in range(9,11):
    print(1)
'''
'''a=Time([0,1,2],format='unix')
print(a[[True,False,True]])
'''
'''
q=Quaternion(0.437548,0.702101, 0.440992, -0.348040)
q2=Quaternion(0.475,0.74,0.37,-0.3)
q3=Quaternion(0.565,0.82,-0.092,0)
a=np.array([0,0,-1])
print(q.rotate(a))

print(type(np.linalg.norm([3,4])))
print(np.inner([1,0,0],[3,4,5]))
'''
a=np.array([0.2,0.2,-1.])
print('{!r,0:.0f}'.format(a))