#!/usr/bin/env python
import rospy
import tf_conversions
from tf.transformations import quaternion_from_euler, euler_from_quaternion
import tf2_ros
import geometry_msgs.msg
from std_msgs.msg import Int8, Int32, Float64
import numpy as np
import sys
from geometry_msgs.msg import Vector3, Quaternion, Transform, TransformStamped
from driving_swarm_msgs.msg import localisation_meta

def create_transform_msg((x,y,z),(qx,qy,qz,qw)):
    t = Transform(Vector3(x,y,z), Quaternion(qx,qy,qz,qw))
    return t

def broadcast_tf(tf_broadcaster, parent, child, transform):
        t = geometry_msgs.msg.TransformStamped()
        t.header.stamp = rospy.Time.now()
        t.header.frame_id = parent
        t.child_frame_id = child
        t.transform = transform
        tf_broadcaster.sendTransform(t)

def update_tf(tf_buffer, tf_broadcaster, bot_count, locSystemName):
    for id in range(bot_count): #0,1,2,..N-1

        # locsystem -> targetN = loc_system -> tb3_N/basefootprint
        tf_from = "loc_system_" + locSystemName
        tf_to = 'tb3_' + str(id+1) + '/base_footprint'
        try: transform_msg = tf_buffer.lookup_transform(tf_from, tf_to, rospy.Time(0))
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException):
            continue #if not possible try next

        transform_msg.header.stamp = rospy.Time.now()
        transform_msg.header.frame_id = tf_from
        transform_msg.child_frame_id = "loc_system_" + locSystemName + "/target" + str(id+1)
        tf_broadcaster.sendTransform(transform_msg)

        #target to tb_N (needed?)
        q = quaternion_from_euler(0, 0, 0)
        broadcast_tf(tf_broadcaster, "loc_system_" + locSystemName + "/target" + str(id+1),
                                     "loc_system_" + locSystemName + "/tb3_" + str(id+1),
                                     (create_transform_msg((0, 0, 0), (q[0], q[1], q[2], q[3]))))

    #TF: world -> loc_system
    q = quaternion_from_euler(0, 0, 0)
    broadcast_tf(tf_broadcaster, 'world', "loc_system_" + locSystemName,
                (create_transform_msg((0, 0, 0), (q[0], q[1], q[2], q[3]))))

def publish_metadata(has_orientation, correct_mapping, accuracy):
    localisation_meta_msg = localisation_meta()
    localisation_meta_msg.has_orientation = has_orientation
    localisation_meta_msg.correct_mapping = correct_mapping
    localisation_meta_msg.accuracy = accuracy
    topic_metadata.publish(localisation_meta_msg);

if __name__ == '__main__':

    
    loc_system_name = "AMCL"

    meta_has_orientation = True
    meta_correct_mapping = True
    meta_accuracy = 1

    rospy.init_node(loc_system_name)
    
    #get params
    bot_count = rospy.get_param('~bot_count')

    #create topic publisher
    topic_metadata = rospy.Publisher('loc_system_meta_' + loc_system_name, localisation_meta,  queue_size=1)

    #create tf buffer
    tf_buffer = tf2_ros.Buffer()
    tf2_ros.TransformListener(tf_buffer)

    #create tf broadcaster
    tf_broadcaster = tf2_ros.TransformBroadcaster()

    rate = rospy.Rate(10) #Hz

    #main loop:
    while not rospy.is_shutdown():
        #update tf
        update_tf(tf_buffer, tf_broadcaster, bot_count, loc_system_name)
        #update meta topic
        publish_metadata(meta_has_orientation, meta_correct_mapping, meta_accuracy)
        rate.sleep()