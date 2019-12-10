#!/usr/bin/env python

# RUNS ON THE TURTLEBOOK

import os
from datetime import datetime

import rospy
import actionlib
import yaml

from core.msg import BehaviourAction, BehaviourGoal
from core.srv import BehaviourAPI

class BehaviourAClient:
    def __init__(self):
        filedir = os.path.dirname(__file__)
        # open behaviour_list which contains all behavs in respective packages
        #pkg_name:
        #  -service_call

        behav_file = open(os.path.join(filedir,'../cfg/behaviour_list.yaml'), 'r')
        self.behav_list = yaml.safe_load(behav_file)
        behav_file.close()

        # mode swiches between interactive mode (tui) and non (.yaml file)
        self.mode = rospy.get_param('~inter_mode', False)

        # timeout for waiting for action clients
        self.action_timeout = rospy.Duration(rospy.get_param('~action_timeout', 60))
        # TODO timeout for TUI?

        # start service / load behaviour_flow for sequencing of behaviours
        if self.mode:
            self.inter_srv = rospy.Service('behaviour_aclient_api', BehaviourAPI, self.api_handler )
            rospy.logwarn('NOT IMPLEMENTED YET')
        else:
            # flow_file must be of type
            # - ['behaviour_name', 'pkg', "['file.launch','arg1:=val','arg2:=val', ...]"]
            # - ['behaviour2_name', ...]
            # (DOUBLE QUOTES (") ARE IMPORTANT HERE)

            flow_file = open(os.path.join(filedir,'../cfg/behaviour_flow.yaml'), 'r')
            self.flow = yaml.safe_load(flow_file)
            flow_file.close()
            #TODO use flow.log
            try:
                os.remove(os.path.join(filedir, '../cfg/flow.log'))
            except:
                rospy.loginfo('[behaviour_aclient]: no old flow.log found')

        # initialise on all servers (turtlebots)
        # TODO TODO
            bot_file = open(os.path.join(filedir,'../cfg/bot_list.yaml'), 'r')
            self.names = yaml.safe_load(bot_file)
            bot_file.close()

            #all action clients
            self.a_clients = []
            #number of bots
            self.no_bots = 0
            for namespace in self.names:
               self.no_bots += 1
               self.a_clients.append(actionlib.SimpleActionClient( '/' + namespace +'/behaviour_aserver', BehaviourAction))

        rospy.logwarn('[behaviour_aclient]: starting with interactive_mode ' + str(self.mode))

        for a_client in self.a_clients:
            rospy.logwarn('[behaviour_aclient]: waiting for ' + a_client.action_client.ns)
            a_client.wait_for_server(timeout=self.action_timeout)
            
        if not self.a_clients:
            rospy.logwarn('a_clients is empty (all unreachable)')
            return 1

        if not self.mode:
            rospy.logwarn("Entering flow mode")
            self.flow_handler()

# TODO TODO check if behav from flow_mode actually in behav_list
# handles behaviour_flow-mode
    def flow_handler(self):
        filedir = os.path.dirname(__file__)
        self.log = open(os.path.join(filedir,'../cfg/flow.log'),'a')

        for flow_item in self.flow:
            self.flow_step = 0
            behav_goal = BehaviourGoal()
            behav_goal.behav_name = flow_item[0]
            behav_goal.behav_pkg = flow_item[1]
            behav_goal.behav_call = flow_item[2]

            rospy.logwarn(flow_item)

            for a_client in self.a_clients:
                rospy.logwarn('Sending to ' + a_client.action_client.ns)
                a_client.send_goal(behav_goal, feedback_cb=self.flow_feedback, done_cb=self.flow_done)

            self.log.write('[' + str(datetime.now().time()) + ']: ' + flow_item[0] + ' with call: ' + flow_item[1])

            rate = rospy.Rate(2)
            rospy.logwarn('Sleep until flow is done')
            while not self.flow_step >= self.no_bots:
                rate.sleep()

            rospy.logwarn('[behaviour_aclient]: moving on to next behaviour in flow')

        rospy.logwarn('[behaviour_aclient]: flow done')
        self.log.close()

    def flow_feedback(self, feedback):
        rospy.logwarn('FEEDBACK')
        self.log.write('['+str(datetime.now().time())+'][' + str(result.ns) + ']: ' + ' PROG[' + feedback.prog_perc + '%] - ' + feedback.prog_status)

    def flow_done(self, term_state, result):
        rospy.logwarn('FLOWDONE ' + str(result.ns))
        succ = 'SUCCESS - ' if result.res_success else 'FAILURE - '
        self.log.write('['+str(datetime.now().time())+'][' + str(result.ns) + ']: ' + ' DONE ' + succ + result.res_msg)
        self.flow_step += 1

# TODO TODO
# handler for api-requests
    def api_handler(self, req):
    # 0 = set a new behav (preempt/replace old one)
    # 1 = get feedback on behav
    # 2 = cancel active behav
    # 3 = try to reconnect bots
    # 3-4 = pause / unpause (in future)
        answer = {'answ_type':0, 'answ_ns':[],'answ_msg':[]}
        # TODO
        if req.req_type == 0:
            # correct yaml is sent by tui (cf flow_file)
            behav = yaml.safe_load(req.req_msg)

            behav = BehaviourGoal()
            behav.behav_name = behav[0]
            behav.behav_pkg = behav[1]
            behav.behav_call = behav[2]
            send_behav()

        return answer
#TODO
    def api_feedback(self, feedback):
        print("WIP")
#TODO
    def api_done(self, result):
        print("WIP")


if __name__ == '__main__':
    rospy.init_node('behaviour_aclient')
    behaviour_aclient = BehaviourAClient()
    rospy.spin()
