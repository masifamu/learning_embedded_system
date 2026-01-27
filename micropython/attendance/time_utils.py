import ntptime
import time

# Example: UTC+5:30 (India)
TIME_OFFSET = 19800  

def sync_time():
    try:
        ntptime.settime()
        print("NTP time synced")
    except:
        print("NTP sync failed")

def get_datetime():
    t = time.localtime(time.time() + TIME_OFFSET)
    date = "{:04d}-{:02d}-{:02d}".format(t[0], t[1], t[2])
    clock = "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5])
    return date, clock
