import cv2
import imutils
import time
import signal
import sys
from Connector import WlanPlugConnector


class ObjectDetection:

    __test_mode = False
    __wait_till_detection = 5
    __threshold = 100000
    __wlan_plug_on = 0
    __wlan_plug_off = 1
    __wait_turn_off = 15
    __cur_cap = False

    def __init__(self):
        self.__WlanPlugConnector = WlanPlugConnector()
        self.__register_abort_signal()

    def __init_window(self):
        cap = cv2.VideoCapture(cv2.CAP_ANY)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.__cur_cap = cap

    def __get_frame(self, s=False):
        cap = self.__cur_cap
        if not cap:
            raise Exception("no window initialized yet")
        _, frame = cap.read()
        frame = imutils.resize(frame, width=500)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if s:
            v = (21, 21)
        else:
            v = (5, 5)

        return cv2.GaussianBlur(frame, v, 0)

    def run(self):
        time_last_movement = False
        _starting_time = time.time()

        cap = self.__init_window()
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

            if threshold.sum() > self.__threshold:
                print(threshold.sum())
                time_last_movement = time.time()
                self.__call_command(self.__wlan_plug_on)
            else:
                if not time_last_movement:
                    continue
                seconds_since_last_movement = int(time.time() - time_last_movement)
                if seconds_since_last_movement > self.__wait_turn_off:
                    self.__call_command(self.__wlan_plug_off)

    def __call_command(self, c):
        if self.__test_mode:
            return
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

