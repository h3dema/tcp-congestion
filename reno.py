
import logging
import numpy as np


# ------------------------------------
#
# Constants for TCP
#
# ------------------------------------
INITIAL_CWND = 1  # Initial congestion window
INITIAL_SSTHRESH = 80  # Arbitrary large value for testing, up to CWND_MAX


class TCPReno:
    def __init__(self, cwnd=INITIAL_CWND, ssthresh=INITIAL_SSTHRESH):
        self.cwnd = cwnd  # Congestion Window (MSS units)
        self.ssthresh = ssthresh  # Slow Start Threshold
        self.dup_ack_count = 0  # Counter for duplicate ACKs
        self.last_ack = None  # Track last ACK received
        self.in_slow_start = True
        self.in_fast_recovery = False
        self.loss_event = False
        self.CWND_MAX = 100  # Maximum congestion window (simulating bandwidth limit)
        self.RTO_THRESHOLD = 3.0  # If no ACKs arrive for 3s, reset cwnd (RTO event)
        logging.debug(f"RENO initialized with cwnd={cwnd}, ssthresh={ssthresh}")

    def update_cwnd(self, ack_time, loss_event=False, timeout=False, dup_ack=False):
        self.loss_event = False
        if timeout:
            # Timeout → Reset to Slow Start
            self.ssthresh = max(self.cwnd // 2, 2)
            self.cwnd = 1
            self.dup_ack_count = 0
            self.in_slow_start = True
            self.in_fast_recovery = False

        elif loss_event:
            # Triple Duplicate ACKs → Fast Recovery
            self.ssthresh = max(self.cwnd // 2, 2)
            self.cwnd = self.ssthresh  # Enter Fast Recovery
            self.in_slow_start = False
            self.in_fast_recovery = True
            self.loss_event = True

        elif self.in_slow_start:
            # Slow Start: Exponential Growth
            self.cwnd *= 2
            if self.cwnd >= self.ssthresh:
                self.in_slow_start = False  # Move to Congestion Avoidance

        elif self.in_fast_recovery:
            # Fast Recovery: Additive Increase (until new ACK)
            self.cwnd += 1  # Temporary inflation during fast recovery

        else:
            # Congestion Avoidance: Additive Increase
            self.cwnd += 1  # Linear growth (1 MSS per RTT)

        # Handle Duplicate ACKs
        if dup_ack:
            if ack_time == self.last_ack:
                self.dup_ack_count += 1
                if self.dup_ack_count == 3:
                    self.update_cwnd(ack_time, loss_event=True)  # Enter Fast Recovery
            else:
                self.dup_ack_count = 0  # Reset if a new ACK arrives

        # Enforce cwnd_max limit
        self.cwnd = min(self.cwnd, self.CWND_MAX)

        # Update last ACK time
        self.last_ack = ack_time

    def __repr__(self):
        return f"TCPReno(cwnd={self.cwnd}, ssthresh={self.ssthresh}, slow_start={self.in_slow_start})"
