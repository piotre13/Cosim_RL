import sys
import logging
from Federate import Federate
import helics as h
import json
import pprint
pp = pprint.PrettyPrinter(indent=4)


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Federate_controller(Federate):
    def __init__(self, args):
        super().__init__(args)
        self.request_time = self.tot_time

        self.observation = []
        self.actions = []
        self.rewards = []

        self.n_episodes = 20
        self.len_episode = 7200
        self.episode = 0
        self.register_endpoints()
    def register_endpoints(self):
        self.ep = list(self.ends.values())[0]
        #subscribe for observation
        self.ep.subscribe('PV/0/Power_PV')
        # logger.debug(f'{pp.pformat(self.init_config)}')
        # for obs in self.init_config['fed_connections']['end'][0]['observations']:
        #     self.ep.subscribe(obs)
        # save targets for reset message

        # save
        pass

    def execution(self):
        h.helicsFederateEnterExecutingMode(self.fed)
        logger.info("\tEntered HELICS execution mode")
        self.granted_time = h.helicsFederateRequestTime(self.fed, self.request_time)
        while self.granted_time <= self.request_time:

            while h.helicsEndpointHasMessage(self.ep):

                # Get the SOC from the EV/charging terminal in question
                msg = h.helicsEndpointGetMessage(self.ep)
                # currentsoc = h.helicsMessageGetString(msg)
                source = h.helicsMessageGetOriginalSource(msg)
                #msg_data = json.loads(msg.data)
                logger.debug(f'\tReceived message from endpoint {source}'
                             f' at time {self.granted_time}'
                             f' with val {msg.data}')



            logger.debug(f'Requesting time {self.tot_time}')
            self.granted_time = h.helicsFederateRequestTime(self.fed, self.tot_time)
            logger.info(f'Granted time: {self.granted_time}')

                # Send back charging command based on current SOC
                #   Our very basic protocol:
                #       If the SOC is less than soc_full keep charging (send "1")
            #     #       Otherwise, stop charging (send "0")
            #     soc_full = 0.95
            #     if float(currentsoc) <= soc_full:
            #         instructions = 1
            #     else:
            #         instructions = 0
            #     message = str(instructions)
            #     h.helicsEndpointSendBytesTo(endid, message.encode(), source)
            #     logger.debug(f'\tSent message to endpoint {source}'
            #                  f' at time {grantedtime}'
            #                  f' with payload {instructions}')
            #
            #     # Store SOC for later analysis/graphing
            #     if source not in soc:
            #         soc[source] = []
            #     soc[source].append(float(currentsoc))
            #
            # time_sim.append(grantedtime)
            #
            # # Since we've dealt with all the messages that are queued, there's
            # #   nothing else for the federate to do until/unless another
            # #   message comes in. Request a time very far into the future
            # #   and take a break until/unless a new message arrives.
            # logger.debug(f'Requesting time {starttime}')
            # grantedtime = h.helicsFederateRequestTime(fed, starttime)
            # logger.info(f'Granted time: {grantedtime}')

    def send_reset(self):
        pass



if __name__ == '__main__':
    fed = Federate_controller(sys.argv)  # giusto da usare quando si runna da helics passando gli argv
    fed.execution()