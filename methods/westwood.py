"""

>>>>>>>>>>>>>>>>>> STILL NEEDS TESTING <<<<<<<<<<<<<<

For example,
python simulation.py --use-westwood --seed 2 --num-acks 10000 --plot-ssthresh

keeps in the maximum value of ssthresh almost in all cases

problem in `self.bw_est` or need to adjust `self.cwnd`

ref. https://en.wikipedia.org/wiki/TCP_Westwood
"""

import logging
import numpy as np

# ------------------------------------
#
# Constants for TCP
#
# ------------------------------------
INITIAL_CWND = 1  # Initial congestion window
INITIAL_SSTHRESH = 80  # Arbitrary large value for testing, up to CWND_MAX

class TCPWestwood:

    def __init__(self, cwnd=INITIAL_CWND, ssthresh=INITIAL_SSTHRESH):
        self.cwnd = cwnd
        self.bw_est = 0  # Estimated bandwidth
        self.ssthresh = ssthresh
        self.last_ack_time = None  # Last received ACK timestamp
        self.CWND_MAX = 100  # Maximum congestion window (simulating bandwidth limit)
        self.loss_event = False
        logging.debug(f"WESTWOOD initialized with cwnd={cwnd}, ssthresh={ssthresh}")

    def update_cwnd(self, ack_time, loss_event=False):
        self.loss_event = False

        if self.last_ack_time is not None and ack_time > self.last_ack_time:
            rtt_sample = ack_time - self.last_ack_time  # Estimate RTT
            if rtt_sample > 0:
                sample_bw = self.cwnd / rtt_sample  # Bandwidth sample
                self.bw_est = 0.9 * self.bw_est + 0.1 * sample_bw  # EWMA filter

        # Store last ACK info
        self.last_ack_time = ack_time

        if loss_event:
            self.ssthresh = min(max(int(self.bw_est * self.ssthresh), 2), self.CWND_MAX)
            print(self.ssthresh, self.cwnd)
            self.cwnd = self.ssthresh  # Enter congestion avoidance
            self.loss_event = True

        else:
            if self.cwnd < self.ssthresh:
                self.cwnd += 1  # Exponential growth (Slow Start)
            else:
                # (Congestion Avoidance)
                self.cwnd += 1.0 / self.cwnd  # Normal Congestion Avoidance (Linear Growth)

        # Enforce cwnd_max limit
        self.cwnd = min(self.cwnd, self.CWND_MAX)

    def __repr__(self):
        return f"TCPWestwood(cwnd={self.cwnd}, bw_est={self.bw_est:.2f})"
