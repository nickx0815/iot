import requests


class WlanPlugConnector:

    __main_path = "http://delock-4004.local/"
    __main_path_cmd = "cm?cmnd=Power%20"
    __on = "On"
    __off = "off"
    __state_wlan_plug = False

    def __init__(self):
        self.turn_off(True)

    def __get_cmd_path(self, c):
        return f"{self.__main_path}{self.__main_path_cmd}{c}"

    def turn_on(self):
        if not self.__state_wlan_plug:
            requests.get(self.__get_cmd_path(self.__on))
            self.__state_wlan_plug = True

    def turn_off(self, force_off=False):
        if self.__state_wlan_plug or force_off:
            requests.get(self.__get_cmd_path(self.__off))
            self.__state_wlan_plug = False

