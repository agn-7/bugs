import threading
import sys

class Dist:
    def __init__(self):
        self.m = threading.Lock()
        self.left = 0
        self.front = 0
        self.raw = []

    #fekkonam kolle idex haye laser 0ta180 daraje 1080ta bashe in stage    
    def update(self, data):
        # these magic numbers were acquired from Alan Beadle 
        # straight ahead is 540, 40 index range should be enough #fekkonam indexe 540, zaviyeye 90 ast dar stage 
        # left chosen to look slightly back to get in front of wall before turning
        def getmin(a, b):
            in_rng = lambda x: data.range_min <= x <= data.range_max
            vsp    = filter(in_rng, data.ranges[a:b])
            if len(vsp) > 0:
                return min(vsp)
            else:                
                return sys.maxint

        #newfront = getmin(500, 581) #commented by agn
        #newleft = getmin(740, 851)
        #in gazebo, laser index is 0:360, then:
        newfront = getmin(160, 200) #zaviyeye 80 ta 100 daraje
        newleft  = getmin(280, 335) #140 daraje ta 167.5 daraje !
        #newleft  = getmin(300, 350) #150 daraje ta 175 daraje !

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
        return (f, l)

    def angle_to_index(self, angle):
        #print("agn6 in angle to index:")
        #print('self.raw.angle_min:', self.raw.angle_min, 'self.raw.angle_increment:', self.raw.angle_increment)
        return int((angle - self.raw.angle_min)/self.raw.angle_increment)

    # angle in radians
    def at(self, angle): #for wall detection
        # TODO(exm): copy and paste programming, refactor later
        def getmin(a, b):
            in_rng = lambda x: self.raw.range_min <= x <= self.raw.range_max
            vsp = filter(in_rng, self.raw.ranges[a:b])
            if len(vsp) > 0:
                #print("hi im in closure . . .")
                return min(vsp)
            else:
                return sys.maxint
        self.m.acquire()
        i = self.angle_to_index(angle) #maybe angle needed global_to_local() in location.py #no this made in should_leave_wall() function
        print("angle=====>", angle, "and i=====>", i)
        #start = i - 40 # for searching  #using for utm hokuyo
        start = i - 40 # for searching  using for urg hokuyo
        if start < 0:
            start = 0
        if start > len(self.raw.ranges): #agn new
            start = len(self.raw.ranges) - 1   
        #end = i + 40   # for searching 
        end = i + 40   # for searching 
        if end >= len(self.raw.ranges):
            end = len(self.raw.ranges) - 1
        if end < 0: #agn new
            end = 0    
        print("start=====>", start, "end=====>", end)    
        ans = getmin(start, end)
        self.m.release()
        return ans
