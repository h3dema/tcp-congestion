import numpy as np
import logging

# ------------------------------------
#
# Constants for TCP
#
# ------------------------------------
INITIAL_CWND = 1  # Initial congestion window
INITIAL_SSTHRESH = 80  # Arbitrary large value for testing, up to CWND_MAX


class TCPAIMD:

    # Constants for AIMD
    MSS = 1  # Maximum Segment Size
    BETA = 0.5  # Multiplicative decrease factor (50% reduction on loss)

    CWND_MAX = 100  # Maximum congestion window (simulating bandwidth limit)
    RTO_THRESHOLD = 3.0  # If no ACKs arrive for 3s, reset cwnd (RTO event)

    def __init__(self, cwnd=INITIAL_CWND, ssthresh=INITIAL_SSTHRESH):
        self.cwnd = cwnd  # Initial congestion window
        self.ssthresh = ssthresh  # Slow start threshold
        self.start_time = None  # Start time of simulation
        self.last_ack_time = None  # Last received ACK time
        self.loss_event = False
        self.in_slow_start = True  # Start in slow start phase
        logging.debug(f"AIMD initialized with cwnd={cwnd}, ssthresh={ssthresh}")

    def update_cwnd(self, ack_time, loss_event=False):
        """Updates cwnd based on AIMD (Slow Start, Additive Increase, Multiplicative Decrease)."""
        if self.start_time is None:
            self.start_time = ack_time  # Set simulation start time
        self.loss_event = False
        # Check for RTO (No ACKs for RTO_THRESHOLD seconds)
        if self.last_ack_time is not None and (ack_time - self.last_ack_time > self.RTO_THRESHOLD):
            # Retransmission Timeout (RTO): If no ACKs arrive in RTO_THRESHOLD seconds, cwnd resets to MSS.
            self.cwnd = self.MSS  # Timeout resets cwnd
            self.ssthresh = self.CWND_MAX
            logging.debug(f"[RTO] Reset cwnd at time {ack_time:.2f}s")
            self.in_slow_start = True  # Reset to slow start

        elif loss_event:
            # Multiplicative Decrease: Cut cwnd by 50%
            self.ssthresh = max(self.ssthresh * self.BETA, self.cwnd + 1, 2)  # Prevent ssthresh from going too low
            self.cwnd = max(self.cwnd * self.BETA, 1)  # Prevent cwnd from reaching 0
            self.loss_event = True
            logging.debug("-- Loss : {:8.4f} {:8.4f} {:6.2f}".format(self.cwnd, self.ssthresh, ack_time))
            self.in_slow_start = True  # Reset to slow start

        elif self.cwnd < self.ssthresh:
            # Slow Start (Exponential Growth)
            self.cwnd += self.MSS
            logging.debug("-- Start: {:8.4f} {:8.4f} {:6.2f}".format(self.cwnd, self.ssthresh, ack_time))

        else:
            # Congestion Avoidance (Additive Increase)
            self.cwnd += self.MSS / self.cwnd  # Linear growth: Add 1 MSS per RTT
            self.ssthresh = max(self.ssthresh, self.cwnd)  # Keep track of max cwnd (not traditional AIMD!)
            logging.debug("-- Avoid: {:8.4f} {:8.4f} {:6.2f}".format(self.cwnd, self.ssthresh, ack_time))

        # Enforce cwnd_max limit
        self.cwnd = min(self.cwnd, self.CWND_MAX)

        # Update last ACK time
        self.last_ack_time = ack_time
