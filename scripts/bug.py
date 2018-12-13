#!/usr/bin/env python

import math
import sys
import rospy
import tf.transformations as transform

from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry

from location import Location, necessary_heading
from dist import Dist

current_location = Location()
current_dists = Dist()

DELTA = .1
WALL_PADDING = .5

STRAIGHT = 0
LEFT = 1
RIGHT = 2
MSG_STOP = 3
RIGHTandSTRAIGHT = 4
LEFTandSTRAIGHT = 5


def init_listener():
    rospy.init_node('listener', anonymous=True)
    rospy.Subscriber('/p3dx/base_pose_ground_truth', Odometry, location_callback)
    rospy.Subscriber('/p3dx/laser/scan', LaserScan, sensor_callback)


def location_callback(data):
    p = data.pose.pose.position
    q = (
            data.pose.pose.orientation.x,
            data.pose.pose.orientation.y,
            data.pose.pose.orientation.z,
            data.pose.pose.orientation.w)
    t = transform.euler_from_quaternion(q)[2]  # In [-pi, pi]
    current_location.update_location(p.x, p.y, t)


def sensor_callback(data):
    current_dists.update(data)


class Bug:
    def __init__(self, tx, ty):
        self.pub = rospy.Publisher('cmd_vel', Twist, queue_size=1)
        self.tx = tx
        self.ty = ty
        self.flag = True

    def go(self, direction):
        cmd = Twist()
        if direction == STRAIGHT:
            cmd.linear.x = 0.3
            cmd.angular.z = 0
        elif direction == LEFT:
            cmd.angular.z = 0.1
        elif direction == RIGHT:
            cmd.angular.z = -0.1
            cmd.linear.x = 0
        elif direction == MSG_STOP:
            cmd.angular.z = 0
            cmd.linear.x = 0
        elif direction == RIGHTandSTRAIGHT:
            print('RIGHTandSTRAIGHT')
            cmd.angular.z = -0.25
            cmd.linear.x = 0.05
        elif direction == LEFTandSTRAIGHT:
            print('RIGHTandSTRAIGHT')
            cmd.angular.z = +0.25
            cmd.linear.x = 0.05
        self.pub.publish(cmd)

    def go_until_obstacle(self):
        print "Going until destination or obstacle"
        while current_location.distance(tx, ty) > DELTA:
            (frontdist, _) = current_dists.get()
            if frontdist <= WALL_PADDING:
                print ("agn8 stop")
                self.go(MSG_STOP)
                return True

            if current_location.facing_point(tx, ty):
                print ("agn9 straight")
                self.go(STRAIGHT)
            elif current_location.faster_left(tx, ty):
                print ("agn10 left")
                self.go(LEFT)
            else:
                print ("agn11 right")
                self.go(RIGHT)
            rospy.sleep(.01)
        return False

    def follow_wall(self):
        print("Wall Following")
        while current_dists.get()[0] <= WALL_PADDING:
            '''zero index is front value that returned in get() function'''
            print('right in zero index')
            self.go(RIGHT)
            rospy.sleep(.01)
        while not self.should_leave_wall():
            '''Wall following started.'''
            (front, left) = current_dists.get()
            if front <= WALL_PADDING:
                print('right')
                self.go(RIGHT)
            elif WALL_PADDING - .1 <= left <= WALL_PADDING + .1:
                print('straight')
                self.go(STRAIGHT)
            elif WALL_PADDING + .1 < left < WALL_PADDING + 1:
                print('lef and straight')
                self.go(LEFTandSTRAIGHT)    
            elif left > WALL_PADDING + .1:
                print('left')
                self.go(LEFT)
            else:
                '''This means left < wall_padding'''
                print('right with else')
                # self.go(RIGHT)
                self.go(RIGHTandSTRAIGHT)
            rospy.sleep(.01)

    def should_leave_wall(self):
        print("You dolt! You need to subclass bug to know how to leave the wall")
        sys.exit(1)


class Bug0(Bug):
    def should_leave_wall(self):
        print('Im in should_leave_wall of bug0')
        (x, y, t) = current_location.current_location()
        dir_to_go = current_location.global_to_local(necessary_heading(x, y, tx, ty))
        '''Direction to goal'''

        print('current_angle:', current_location.current_location()[2])
        print('desired_angle_without_global_to_local:', necessary_heading(x, y, tx, ty))
        print('desired_angle:', dir_to_go)
        at = current_dists.at(dir_to_go)
        if at > 10:
            print('flag', self.flag)
            print("Leaving wall in at")
            return True
        return False


class Bug1(Bug):
    def __init__(self, tx, ty):
        Bug.__init__(self, tx, ty)
        self.closest_point = (None, None)
        self.origin = (None, None)
        self.circumnavigated = False

    def face_goal(self):
        """such as bug2"""
        while not current_location.facing_point(self.tx, self.ty):
            print('in face goal2 and turn right')
            self.go(RIGHT)
            rospy.sleep(.01)

    def follow_wall(self):
        """such as bug2"""
        Bug.follow_wall(self)
        self.face_goal()      

    def should_leave_wall(self):
        (x, y, t) = current_location.current_location()

        if None in self.closest_point:
            self.origin = (x, y)
            self.closest_point = (x, y)
            self.closest_distance = current_location.distance(self.tx, self.ty)
            '''get once distance for each obstacle'''

            self.left_origin_point = False
            return False
        d = current_location.distance(self.tx, self.ty)
        if d < self.closest_distance:
            print "New closest point at", (x, y)
            self.closest_distance = d
            '''closest distance updated'''

            self.closest_point = (x, y)

        (ox, oy) = self.origin
        if not self.left_origin_point and not near(x, y, ox, oy):
            print "Left original touch point"
            self.left_origin_point = True
        elif near(x, y, ox, oy) and self.left_origin_point:
            '''circumnavigation achieved!'''
            print("Circumnavigated obstacle")
            self.circumnavigated = True

        (cx, cy) = self.closest_point
        if self.circumnavigated and near(x, y, cx, cy):
            '''achieve nearest point after a circumnavigated obstacle'''

            self.closest_point = (None, None)
            '''Init for next obstacle.'''

            self.origin = (None, None)
            self.circumnavigated = False
            self.left_origin_point = False
            print("Leaving wall")
            return True

        else:
            return False


class Bug2(Bug):
    def __init__(self, tx, ty):
        Bug.__init__(self, tx, ty)
        self.lh = None
        self.encountered_wall_at = (None, None)

    def face_goal(self):
        while not current_location.facing_point(self.tx, self.ty):
            print('in face goal2 and turn right')
            self.go(RIGHT)
            rospy.sleep(.01)

    def follow_wall(self):
        Bug.follow_wall(self)
        self.face_goal()

    def should_leave_wall(self):
        (x, y, _) = current_location.current_location()

        if None in self.encountered_wall_at:
            self.encountered_wall_at = (x, y)
            self.lh = necessary_heading(x, y, self.tx, self.ty)
            '''get degree once'''
            return False

        t_angle = necessary_heading(x, y, self.tx, self.ty)
        '''get degree while the robot is following the wall '''

        (ox, oy) = self.encountered_wall_at
        od = math.sqrt((ox - self.tx)**2 + (oy - self.ty)**2)
        '''origin to goal distance'''

        cd = math.sqrt((x - self.tx)**2 + (y - self.ty)**2)
        '''current to goal distance'''

        dt = 0.01

        if self.lh - dt <= t_angle <= self.lh + dt and not near(x, y, ox, oy):
            '''Makes robot placed on origin to goal planned (Bug2 algorithm)'''
            if cd < od:
                print "Leaving wall"
                self.encountered_wall_at = (None, None)
                '''Init for another obstacle'''
                return True
        return False


def near(cx, cy, x, y):
    nearx = x - .3 <= cx <= x + .3
    neary = y - .3 <= cy <= y + .3
    return nearx and neary  # Only if nearx and neary are true, return is true.


def bug_algorithm(bug):
    init_listener()
    cmd = Twist()
    pub = rospy.Publisher('cmd_vel', Twist, queue_size=1)
    print("Calibrating sensors...")
    '''This actually just lets the sensor readings propagate into the system'''
    rospy.sleep(1)
    print("Calibrated")

    while current_location.distance(tx, ty) > DELTA:
        hit_wall = bug.go_until_obstacle()
        if hit_wall and bug.flag:
            '''arrive to the wall or obstacle'''
            print('near wall following', bug.flag)
            bug.follow_wall()
    print("Arrived at", (tx, ty))
    cmd.linear.x = 0
    cmd.angular.z = 0
    pub.publish(cmd)


if __name__ == '__main__':
    '''Parse arguments'''
    algorithm = sys.argv[1]
    algorithms = ["bug0", "bug1", "bug2"]
    if algorithm not in algorithms:
        print("First argument should be one of ", algorithms, ". Was ", algorithm)
        sys.exit(1)

    if len(sys.argv) < 4:
        print("Usage: rosrun bugs bug.py ALGORITHM X Y")
        sys.exit(1)
    (tx, ty) = map(float, sys.argv[2:4])

    print("Setting target:", (tx, ty))
    bug = None
    if algorithm == "bug0":
        bug = Bug0(tx, ty)
    elif algorithm == "bug1":
        bug = Bug1(tx, ty)
    elif algorithm == "bug2":
        bug = Bug2(tx, ty)

    bug_algorithm(bug)
