import threading
import math
import sys

# Location is used to maintain a single current location of the robot in a
# thread-safe manner such that the callback and readers can all use it without
# issue
class Location:
    def __init__(self):
        self.m = threading.Lock() # global lock b/c easy and not a problem yet
        self.x = None
        self.y = None
        self.t = None
        self.deltaT = 0.05 # how close to angle to be to go

    def update_location(self, x, y, t):
        self.m.acquire()
        self.x = x
        self.y = y
        self.t = t
        self.m.release()

    def current_location(self):
        self.m.acquire()
        x = self.x
        y = self.y
        t = self.t
        self.m.release()
        return (x, y, t)

    def distance(self, x, y):
        (x0, y0, _) = self.current_location()
        if x0 == None or y0 == None:
            # will be none on the first iteration
            print("hi agn1")
            return sys.maxint
        return math.sqrt((x-x0)**2 + (y-y0)**2)

    def facing_point(self, x, y):
        (cx, cy, current_heading) = self.current_location()
        if None in (cx, cy, current_heading):
            print("hi agn2 false")
            return False
        n = necessary_heading(cx, cy, x, y)
        # TODO(exm) possible bug with boundary conditions?
        #print("hi agn3")
        return n - self.deltaT <= current_heading <= n + self.deltaT #if true--> going straight

    def faster_left(self, x, y):
        (cx, cy, current_heading) = self.current_location()
        if None in (cx, cy, current_heading):
            print("agn12 hi im here false")
            return False
        #print("hi agn4 want to turn right/left")    
        #print('current_heading :', current_heading , 'necessary_heading',necessary_heading(cx, cy, x, y))
        return current_heading - necessary_heading(cx, cy, x, y) < 0 #if true-->go to left if false-->go to right

    def global_to_local(self, desired_angle): 
        (_, _, current_heading) = self.current_location()
        ans = desired_angle - current_heading
        if ans < -math.pi:
            ans += 2* math.pi #for example: if theta=-270 ==> theta = -270 + 360 = 90 #baraye inke theta bayad beyne -pi ta pi bashe
        elif ans > math.pi: #agn new
            ans -= 2*math.pi      
        return ans


# current x, y; target x,y
def necessary_heading(cx, cy, tx, ty):
    return math.atan2(ty-cy, tx-cx)
