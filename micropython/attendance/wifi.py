import network
import time

# CHANGE THESE
STA_SSID = "esp32cam_wifi"
STA_PASSWORD = "esp32cam"

def start_wifi():
    # Station mode (for NTP)
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        sta.connect(STA_SSID, STA_PASSWORD)
        for _ in range(20):
            if sta.isconnected():
                break
            time.sleep(1)

    print("STA connected:", sta.isconnected())

    # Access Point (for students)
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(
        essid="ESP32-Attendance",
        password="attendance123",
        authmode=network.AUTH_WPA_WPA2_PSK
    )

    print("AP IP:", ap.ifconfig()[0])
