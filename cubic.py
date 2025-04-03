import logging
import numpy as np


# ------------------------------------
#
# Constants for TCP
#
# ------------------------------------
INITIAL_CWND = 1  # Initial congestion window
INITIAL_SSTHRESH = 80  # Arbitrary large value for testing, up to CWND_MAX


class TCPCubic:

    # Constants for CUBIC
    MSS = 1  # Maximum Segment Size
    C = 0.4  # CUBIC scaling factor
    BETA = 0.7  # Multiplicative decrease factor

    CWND_MAX = 100  # Maximum congestion window (simulating bandwidth limit)
    RTO_THRESHOLD = 3.0  # If no ACKs arrive for 3s, reset cwnd (RTO event)

    def __init__(self, cwnd=INITIAL_CWND, ssthresh=INITIAL_SSTHRESH):
        self.cwnd = cwnd  # Initial congestion window
        self.ssthresh = ssthresh  # Slow start threshold
        self.W_max = None  # Previous max window size
        self.last_loss_time = None  # Time of last loss
        self.start_time = None  # Start time of simulation
        self.last_ack_time = None  # Last received ACK time
        self.loss_event = False
        logging.debug(f"CUBIC initialized with cwnd={cwnd}, ssthresh={ssthresh}")

    def cubic_wnd(self, t):
        """CUBIC function: calculates new cwnd based on time t since last loss."""
        if self.W_max is None:
            self.W_max = self.cwnd
        K = ((self.W_max * (1 - self.BETA)) / self.C) ** (1/3)
        return self.C * ((t - K) ** 3) + self.W_max

    def update_cwnd(self, ack_time, loss_event=False):
        """Updates cwnd based on slow start, congestion avoidance, or loss."""
        if self.start_time is None:
            self.start_time = ack_time  # Set simulation start time
        self.loss_event = False

        elapsed_time = ack_time - self.start_time

        # Check for RTO (No ACKs for RTO_THRESHOLD seconds)
        if self.last_ack_time is not None and (ack_time - self.last_ack_time > self.RTO_THRESHOLD):
            # Retransmission Timeout (RTO): If no ACKs arrive in RTO_THRESHOLD seconds, cwnd resets to MSS.
            self.cwnd = self.MSS  # Timeout resets cwnd
            # self.ssthresh = max(self.cwnd // 2, 2)
            print(f"[RTO] Reset cwnd at time {ack_time:.2f}s")

        elif loss_event:
            # Multiplicative Decrease
            self.W_max = self.cwnd  # Save previous cwnd before reduction
            self.cwnd *= self.BETA  # Reduce window size
            self.ssthresh = max(self.cwnd, 1)  # Adjust threshold
            self.last_loss_time = elapsed_time  # Track last loss event
            # print(f"Loss event at time {ack_time:.2f}s")
            self.loss_event = True

        elif self.cwnd < self.ssthresh:
            # Slow Start (Exponential Growth)
            self.cwnd += self.MSS

        else:
            # Congestion Avoidance (CUBIC Growth)
            self.cwnd = max(self.cubic_wnd(elapsed_time), self.MSS)  # Ensure minimum cwnd

        # Enforce cwnd_max limit
        self.cwnd = min(self.cwnd, self.CWND_MAX)

        # Update last ACK time
        self.last_ack_time = ack_time
