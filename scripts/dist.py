import threading
import sys


class Dist:
    def __init__(self):
        self.m = threading.Lock()
        self.left = 0
        self.front = 0
        self.raw = []

    def update(self, data):
        """
        left chosen to look slightly back to get in front of wall before turning
        :param data: laser raw data.
        :return:
        """
        def getmin(a, b):
            in_rng = lambda x: data.range_min <= x <= data.range_max
            vsp = filter(in_rng, data.ranges[a:b])
            if len(vsp) > 0:
                return min(vsp)
            else:                
                return sys.maxint

        '''in gazebo, laser index is 0:360'''
        newfront = getmin(160, 200)  # 80 to 100 degree
        newleft = getmin(280, 335)  # 140 to 167.5 degree!
        # newleft = getmin(300, 350)  # 150 to 175 degree!

        self.m.acquire()
        self.left = newleft
        self.front = newfront
        self.raw = data
        self.m.release()

    def get(self):
        self.m.acquire()
        l = self.left
        f = self.front
        self.m.release()
        return f, l

    def angle_to_index(self, angle):
        return int((angle - self.raw.angle_min) / self.raw.angle_increment)

    # angle in radians
    def at(self, angle):
        """for wall detection"""

        def getmin(a, b):
            in_rng = lambda x: self.raw.range_min <= x <= self.raw.range_max
            vsp = filter(in_rng, self.raw.ranges[a:b])
            if len(vsp) > 0:
                return min(vsp)
            else:
                return sys.maxint
        self.m.acquire()
        i = self.angle_to_index(angle)
        # TODO : maybe angle needed global_to_local() in location.py
        # TODO : no this made in should_leave_wall() function
        print("angle=====>", angle, "and i=====>", i)
        start = i - 40  # For searching using for urg hokuyo
        if start < 0:
            start = 0
        if start > len(self.raw.ranges):
            start = len(self.raw.ranges) - 1
        end = i + 40   # for searching 
        if end >= len(self.raw.ranges):
            end = len(self.raw.ranges) - 1
        if end < 0:
            end = 0    
        print("start=====>", start, "end=====>", end)    
        ans = getmin(start, end)
        self.m.release()
        return ans
