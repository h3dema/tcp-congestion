"""

>>>>>>>>>>>>>>>>>>>>>> NOT USED <<<<<<<<<<<<<<<<<<<<<<<<

Uses RTT instead of ACKS

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


class TCPHyStart:
    def __init__(self, cwnd=1, ssthresh=64):
        self.cwnd = cwnd  # Initial congestion window (MSS units)
        self.ssthresh = ssthresh  # Slow Start Threshold
        self.min_rtt = float("inf")  # Track min RTT
        self.prev_rtt = None  # Previous RTT value
        self.in_slow_start = True  # Start in Slow Start
        self.delay_threshold = 1.25  # RTT increase threshold (1.25x min RTT)
        self.ack_count = 0  # Track number of ACKs
        self.CWND_MAX = 100  # Maximum congestion window (simulating bandwidth limit)
        self.loss_event = False
        logging.debug(f"RENO initialized with cwnd={cwnd}, ssthresh={ssthresh}")

    def update_cwnd(self, ack_time, rtt, loss_event=False):
        self.ack_count += 1

        # Update min RTT (for delay-based detection)
        if rtt < self.min_rtt:
            self.min_rtt = rtt

        # Loss-based exit from slow start
        if loss_event:
            self.ssthresh = max(self.cwnd // 2, 2)
            self.cwnd = self.ssthresh
            self.in_slow_start = False  # Enter congestion avoidance
            self.loss_event = True

        # Delay-based exit from slow start
        elif self.in_slow_start and self.prev_rtt is not None:
            if rtt > self.min_rtt * self.delay_threshold:  # RTT increase detected
                self.ssthresh = self.cwnd  # Set ssthresh to current cwnd
                self.in_slow_start = False  # Exit slow start

        # Normal Slow Start (Exponential Growth)
        if self.in_slow_start:
            self.cwnd *= 2  # Double cwnd every RTT
        else:
            # Congestion Avoidance (Additive Increase)
            self.cwnd += 1  # Linear growth after slow start

        # Enforce cwnd_max limit
        self.cwnd = min(self.cwnd, self.CWND_MAX)

        # Store last RTT
        self.prev_rtt = rtt

    def __repr__(self):
        return f"TCPHyStart(cwnd={self.cwnd}, ssthresh={self.ssthresh}"
