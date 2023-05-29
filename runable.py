import requests
import cv2
import imutils
import time
import signal
import sys
import argparse


class WlanPlugConnector:
    __main_path = "http://delock-4004.local/"
    __main_path_cmd = "cm?cmnd=Power%20"
    __on = "On"
    __off = "off"
    __state_wlan_plug = False

    def __init__(self, test_mode):
        self.turn_off(True)
        self.__test_mode = test_mode

    def __get_cmd_path(self, c):
        return f"{self.__main_path}{self.__main_path_cmd}{c}"

    def turn_on(self):
        if not self.__state_wlan_plug and not self.__test_mode:
            requests.get(self.__get_cmd_path(self.__on))
            self.__state_wlan_plug = True

    def turn_off(self, force_off=False):
        if self.__state_wlan_plug or force_off:
            requests.get(self.__get_cmd_path(self.__off))
            self.__state_wlan_plug = False


class ObjectDetection:
    __cur_cap = False
    __wlan_plug_on = 0
    __wlan_plug_off = 1
    _default_wait = 5
    _default_threshold_low = 1000
    _default_threshold_high = 100000000
    _default_wait_off = 10

    def __init__(self,
                 test_mode=True,
                 wait=_default_wait,
                 threshold_low=_default_threshold_low,
                 threshold_high=_default_threshold_high,
                 wait_off=_default_wait_off):
        self.__WlanPlugConnector = WlanPlugConnector(test_mode)
        self.__register_abort_signal()
        self.__wait_till_detection = wait
        self.__threshold_low = threshold_low
        self.__threshold_high = threshold_high
        self.__wait_turn_off = wait_off

    def __init_window(self):
        cap = cv2.VideoCapture(cv2.CAP_ANY)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.__cur_cap = cap

    def __get_frame(self, start_frame=False):
        cap = self.__cur_cap
        if not cap:
            raise Exception("no window initialized yet")
        _, frame = cap.read()
        frame = imutils.resize(frame, width=500)
        #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if start_frame:
            v = (21, 21)
        else:
            v = (5, 5)
        return cv2.GaussianBlur(frame, v, 0)

    def __get_window(self):
        return self.__cur_cap

    def run(self):
        time_last_movement = False
        _starting_time = time.time()

        self.__init_window()
        cap = self.__get_window()
        if not cap.isOpened():
            return

        start_frame = self.__get_frame(True)

        while True:

            if self.__skip(_starting_time):
                continue

            _, frame = cap.read()
            frame_bw = self.__get_frame()
            difference = cv2.absdiff(frame_bw, start_frame)
            threshold = cv2.threshold(difference, 25, 255, cv2.THRESH_BINARY)[1]
            start_frame = frame_bw
            if self.__threshold_low < threshold.sum() < self.__threshold_high:
                print(threshold.sum())
                time_last_movement = time.time()
                self.__call_command(self.__wlan_plug_on)
            else:
                if not time_last_movement:
                    continue
                if int(time.time() - time_last_movement) > self.__wait_turn_off:
                    self.__call_command(self.__wlan_plug_off)

    def __call_command(self, c):
        if c == self.__wlan_plug_on:
            self.__turn_wlan_plug_on()
        elif c == self.__wlan_plug_off:
            self.__turn_wlan_plug_off()
        else:
            raise Exception("command not found")

    def __register_abort_signal(self):
        def signal_handler(sig, frame):
            self.__turn_wlan_plug_off()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

    def __skip(self, start_time):
        _frame_time = time.time()
        __up_time = int(_frame_time - start_time)
        if self.__wait_till_detection > __up_time:
            return True
        else:
            return False

    def __turn_wlan_plug_on(self):
        self.__WlanPlugConnector.turn_on()

    def __turn_wlan_plug_off(self):
        self.__WlanPlugConnector.turn_off()


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_mode', dest="test_mode", type=str2bool)
    parser.add_argument('--wait', dest='wait', type=int, default=ObjectDetection._default_wait)
    parser.add_argument('--threshold_low', dest='threshold_low', type=int,
                        default=ObjectDetection._default_threshold_low)
    parser.add_argument('--threshold_high', dest='threshold_high', type=int,
                        default=ObjectDetection._default_threshold_high)
    parser.add_argument('--wait_off', dest='wait_off', type=int, default=ObjectDetection._default_wait_off)
    args = parser.parse_args()
    ObjectDetection(test_mode=args.test_mode, wait_off=args.wait_off, wait=args.wait, threshold_low=args.threshold_low,
                    threshold_high=args.threshold_high).run()

