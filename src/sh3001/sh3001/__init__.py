#!/usr/bin/env python3
from sh3001.sh3001 import Sh3001
from sh3001.i2c import I2C

def run_command(cmd=""):
    import subprocess
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read().decode('utf-8')
    status = p.poll()
    # print(result)
    # print(status)
    return status, result

def do(msg="", cmd=""):
    print(" - %s..." % (msg), end='\r')
    print(" - %s... " % (msg), end='')
    status, result = eval(cmd)
    # print(status, result)
    if status == 0 or status == None or result == "":
        print('Done')
    else:
        print('Error')
        errors.append("%s error:\n  Status:%s\n  Error:%s" %
                      (msg, status, result))

class LxAutoStart(object):
    ''' 
        To setup /home/pi/.config/lxsession/LXDE-pi/autostart
    '''

    def __init__(self, file="/home/pi/.config/lxsession/LXDE-pi/autostart"):
        try:
            self.file = file
            with open(self.file, 'r') as f:
                cmdline = f.read()
            self.cmdline = cmdline.strip()
            self.cmds = self.cmdline.split('\n')
        except FileNotFoundError:
            self.file = file
            conf = open(self.file,'w')
            conf.write("")
            conf.close()
            self.cmds = []

    def remove(self, expected):
        for cmd in self.cmds:
            if expected in cmd:
                self.cmds.remove(cmd)
        return self.write_file()

    def set(self, cmd):
        have_excepted = False
        for tmp in self.cmds:
            if tmp == cmd:
                have_excepted = True
                break

        if not have_excepted:
            self.cmds.append(cmd)
        return self.write_file()

    def write_file(self):
        try:
            cmdline = '\n'.join(self.cmds)
            # print(cmdline)
            with open(self.file, 'w') as f:
                f.write(cmdline)
            return 0, cmdline
        except Exception as e:
            return -1, e


def usage():
    print("Usage auto-rotator [install/uninstall/calibrate]")
    quit()

def calibrate(reset=False):

    sensor = Sh3001(db='/home/pi/.config/auto-rotator/config')
    if reset:
        sensor.acc_max = [0, 0, 0]
        sensor.acc_min = [0, 0, 0]
        sensor.acc_offset = [0, 0, 0]

    try:
        print('Calibration start!')
        print('Rotate the device for 720 degree in all 3 axis')
        print('Crtl + C to quit if finished')
        while True:
            sensor.calibrate('acc')
    except KeyboardInterrupt:
        print("")
        sensor.set_offset()
        print("Calibrate successfully")
        print('Offset: %s' % sensor.acc_offset)
        quit()


def rotate():
    import time
    from math import asin
    import math
    import sys
    from sh3001.filedb import fileDB

    lxAutoStart = LxAutoStart()
    db = fileDB(db='/home/pi/.config/auto-rotator/config')
    if len(sys.argv) >= 2:
        if sys.argv[1] == "install":
            _, result = run_command("ls /home/pi/.config")
            if "raspad" not in result:
                lxAutoStart.set("@lxpanel --profile LXDE-pi")
                lxAutoStart.set("@pcmanfm --desktop --profile LXDE-pi")
                lxAutoStart.set("@xscreensaver -no-splash")
                lxAutoStart.set("@auto-rotator")

            else:
                lxAutoStart.set("@auto-rotator")
            print("auto-rotator installed successfully")

            if len(sys.argv) == 3:
                if sys.argv[2] in ["180", "90"]:
                    db.set("rotate_angle", sys.argv[2])
                else:
                    usage()
            quit()
        elif sys.argv[1] == "uninstall":
            lxAutoStart.remove("@auto-rotator")
            print("auto-rotator uninstalled successfully")
            quit()
        elif sys.argv[1] == "calibrate":
            reset = False
            if len(sys.argv) >= 3:
                sys.argv[2] == "reset"
                reset = True
            calibrate(reset=reset)
        else:
            usage()

    rotate_angle = db.get("rotate_angle", "90")
    sensor = Sh3001(db='/home/pi/.config/auto-rotator/config')

    while True:
        try:
            acc_list = sensor.sh3001_getimudata('acc','xyz')
        except IOError:
            print("read module error.")
            time.sleep(1)
            continue
        # print(acc_list)
        acc_list = [min(2046,i) for i in acc_list]
        acc_list = [max(-2046,i) for i in acc_list]
        # print(asin(acc_list[0] / 2100.0))
        current_angle_x = (asin(acc_list[0] / 2046.0)) / math.pi * 180
        current_angle_y = (asin(acc_list[1] / 2046.0)) / math.pi * 180
        # print((asin(acc_list[1] / 2046.0)) / math.pi * 180)
        time.sleep(0.1)
        # print("current_angle_x: ",current_angle_x)
        # print("current_angle_y: ",current_angle_y)
        if current_angle_y > 45:
            # print("normal")
            run_command("rotate-helper normal")
        elif current_angle_y < -45:
            # print("inverted")
            run_command("rotate-helper inverted")
        elif rotate_angle == "90":
            if current_angle_x > 45:
                # print("left")
                run_command("rotate-helper left")

            elif current_angle_x < -45:
                # print("right")
                run_command("rotate-helper right")
            else:
                pass
                # print("no")
        else:
            pass
            # print("no")
        time.sleep(1)

if __name__ == '__main__':
#     # run_command("rotate-helper normal")
    while True:
        rotate()
