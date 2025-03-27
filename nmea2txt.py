"""
    this python script was written studens of the course Intelligent Transportation SystemError
    to evaulate nmea files recorded by u-blox f9p RTK GNSS receiver
    written by Bence Takács
    last modified 7 March 2027
"""
import sys
import re
from math import pi, cos
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

def checksum(buf):
    """ check nmea checksum on line """
    cs = ord(buf[1])
    for ch in buf[2:-3]:
        cs ^= ord(ch)
    ch = '0' + re.sub('^0x', '', hex(cs))
    return ch[-2:].upper()

def nmea2deg(nmea):
    """ convert nmea angle (dddmm.mm) to degree """
    pos = nmea.find('.')
    return int(nmea[:pos-2]) + float(nmea[pos-2:]) / 60.0

def plot_data(data, fout):
    """ plot relevant figure """
    # print elevation versus time
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(data['datetime'], data['ele'])
    ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))
    ax.grid()
    ax.set_xlabel('time (hh:mm)')
    ax.set_ylabel('elevation [meter]')
    ax.set_title('all positions')
    plt.savefig(fout + '_ele.png')
    plt.close()

    # print number of satellites versus time
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(data['datetime'], data['nsat'])
    ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))
    ax.grid()
    ax.set_xlabel('time (hh:mm)')
    ax.set_ylabel('number of satellites')
    plt.savefig(fout + '_nsat.png')
    plt.close()

    # filter out only fix rows
    data_fix = data[data['sol_mode'].str.contains('R', na=False)]

    # print elevation versus time, just fixed positions
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(data_fix['datetime'], data_fix['ele'])
    ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))
    ax.grid()
    ax.set_xlabel('time (hh:mm)')
    ax.set_ylabel('elevation [meter]')
    ax.set_title('fix positions')
    plt.savefig(fout + '_ele_fix.png')
    plt.close()

    # convert latitude and longitude deviations from mean fix positions to meter
    #ezek nem pontos koordináták!!!
    lat = data_fix['lat'].mean()
    lon = data_fix['lon'].mean()
    ele = data_fix['ele'].mean()

    dlat = pi / 180 * 6380000 / 3600
    dlon = dlat * cos(lat / 180 * pi)

    data['dlat'] = (data['lat'] - lat) * dlat * 3600 * 1000
    data['dlon'] = (data['lon'] - lon) * dlon * 3600 * 1000
    data['dele'] = (data['ele'] - ele) * 1000

    # filter out only fix rows
    data_fix = data[data['sol_mode'].str.contains('R', na=False)]

    # scatter of only fixed positions
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.scatter(data_fix['dlon'], data_fix['dlat'], marker='o')
    ax.grid()
    ax.set_xlabel('delta east [mm]')
    ax.set_ylabel('delta north [mm]')
    ax.set_title('fix positions')
    ax.axis('equal')
    xmin = ax.get_xlim()[0]
    ymin = ax.get_ylim()[0]
    ax.text(xmin, ymin, f"mean position: {lat:.8f} {lon:.8f}", style='italic')
    plt.savefig(fout + '_scat.png')
    plt.close()

if __name__ == "__main__":
    #check number of command line arguments
    if len(sys.argv) != 2:
        print('use', sys.argv[0], 'nmea_file_name')
        exit()

    #input file name with nmea logs
    fname1 = sys.argv[1]

    #output file name
    dot_index = fname1.rfind('.')
    fname2 = fname1[:dot_index] + '_.txt'
    fout_plot = fname1[:dot_index]

    fi = open(fname1, 'r') # open input file
    fo = open(fname2, 'w') # open input file
    df = pd.DataFrame(columns = ["datetime", "lat", "lon", "ele", "nsat", "sol_mode"])
    for line in fi: #loop over lines in the file
        line = line.strip()
        if re.match(r'\$..ZDA', line):
            zda = line.split(',')
            y = int(zda[4])
            m = int(zda[3])
            d = int(zda[2])
            break

    for line in fi: #loop over lines in the file
        line = line.strip()
        if checksum(line) != line[-2:]:
            print("Chechsum error: " + line)
            continue
        if re.match(r'\$..GNS', line):
            gga = line.split(',')
            if gga[2] == '':
                continue
            lat = nmea2deg(gga[2])
            if gga[3].upper() == 'S':
                lat *= -1
            lon = nmea2deg(gga[4])
            if gga[3].upper() == 'W':
                lon *= -1
            nsat = int(gga[7])
            ele = float(gga[9])
            sol_type = gga[6]
            hh = int(gga[1][0:2])
            mm = int(gga[1][2:4])
            ss = int(gga[1][4:6])
            mydate = datetime.datetime(y, m, d, hh, mm, ss)
            print(f'{mydate} {lat:.8f} {lon:.8f} {ele:.3f} {nsat:.0f} {sol_type:4s}', file = fo)
            df = pd.concat([df, pd.DataFrame([{'datetime' : mydate, 'lat' : lat, 'lon' : lon, 'ele' : ele, 'nsat' : nsat, 'sol_mode' : sol_type}])],
                    ignore_index = True)

    fi.close()
    fo.close()

    # plot coordinate errors
    plot_data(df, fout_plot)
