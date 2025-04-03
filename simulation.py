import argparse
import random
import numpy as np
import matplotlib.pyplot as plt

from methods.cubic import TCPCubic
from methods.aimd import TCPAIMD
from methods.reno import TCPReno


INITIAL_CWND = 1  # Initial congestion window
INITIAL_SSTHRESH = 100  # Arbitrary large value for testing

#
# Simulator Constants
#
MAX_LOSS_PROB = 0.25  # Maximum loss probability allowed in the simulation
ACK_TIME_SATURATION_DELAY: float = 0.1


# ACK Generator with Loss, Jitter, and Link Saturation
def generate_ack_array(num_acks=100, base_interval=0.1, loss_prob=0.1, jitter=0.02, saturation_event=80, seed=None):
    """
    Generates an array of (ACK_number, arrival_time, loss_event).

    Parameters:
    - `num_acks`: Number of ACKs to generate.
    - `base_interval`: Average time between ACKs.
    - `loss_prob`: Probability of an ACK being lost.
    - `jitter`: Random delay added to ACK arrival time.
    - `saturation_event`: After this many ACKs, we introduce a temporary congestion burst.
    - `seed`: Optional seed for the random number generator.

    Returns:
    - An array of (ACK_number, arrival_time, loss_event).
    """
    if seed is not None and isinstance(seed, int):
        random.seed(seed)

    ack_array = []
    current_time = 0.0
    link_saturation = False  # Flag to simulate heavy congestion

    loss_prob = min(loss_prob, MAX_LOSS_PROB)  # limit max loss in the network

    for i in range(1, num_acks + 1):
        # Introduce random jitter
        ack_time = current_time + base_interval + random.uniform(-jitter, jitter)

        # Simulate packet loss
        loss_event = random.random() < loss_prob

        # Introduce link saturation: Large delay in transmission (e.g., congestion event)
        if i == saturation_event:
            ack_time += ACK_TIME_SATURATION_DELAY  # Large delay simulating queue buildup
            link_saturation = True
            # loss_prob += 0.01  # Increase loss probability during congestion

        elif link_saturation:
            # Gradual recovery after congestion burst
            ack_time += 0.05
            # loss_prob = min(loss_prob * 1.1, MAX_LOSS_PROB)  # Increase loss probability over time

        # Append the (ACK_number, time, loss) to array
        ack_array.append((i, ack_time, loss_event))

        # Move time forward
        current_time = ack_time

    return ack_array


def simulate(tcp, ack_array):
    """
    Simulates the entire TCP congestion process given an array of ACKs.

    Parameters:
    - `tcp`: TCP congestion control object to be simulated.
    - `ack_array`: Array of traffic (ACK_number, time, loss_event) to be processed.

    Returns:
    - `time_stamps`: Array of times corresponding to each ACK.
    - `cwnd_evolution`: Array of congestion window values over time.
    - `loss_events`: Array of loss events (1 if loss, 0 otherwise).
    - `ssthreshs`: Array of slow-start thresholds over time.
    """
    cwnd_evolution = []
    time_stamps = []
    loss_events = []
    ssthreshs = []

    for i, (ack_num, ack_time, loss_event) in enumerate(ack_array):
        tcp.update_cwnd(ack_time, loss_event)

        # Store results
        cwnd_evolution.append(tcp.cwnd)
        time_stamps.append(ack_time)
        loss_events.append(1 if tcp.loss_event else 0)
        ssthreshs.append(tcp.ssthresh)

    return time_stamps, cwnd_evolution, loss_events, ssthreshs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--use-aimd', action='store_true', help="Use TCP AIMD congestion control")
    group.add_argument('--use-cubic', action='store_true', help="Use TCP Cubic congestion control")
    group.add_argument('--use-reno', action='store_true', help="Use TCP Reno congestion control")

    parser.add_argument('--num-acks', type=int, default=10_000, help='Number of ACKs to simulate')

    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--cwnd', type=int, default=INITIAL_CWND)
    parser.add_argument('--ssthresh', type=int, default=INITIAL_SSTHRESH)

    parser.add_argument('--loss-prob', type=float, default=0.01, help='Probability to loose an ACK')

    parser.add_argument('--plot-acks', action='store_true', help="add the ACKs (markers) in the plot")
    parser.add_argument('--hide-acks', action='store_false', help="hide ACK markers (default)")
    parser.set_defaults(plot_acks=False)

    parser.add_argument('--plot-ssthresh', action='store_true', help="show the progression of the ssthread threshold")
    parser.add_argument('--hide-ssthresh', action='store_false', help="hide the progression of the ssthread threshold (default)")
    parser.set_defaults(plot_ssthresh=False)

    parser.add_argument('--plot-lost', action='store_true', help="show the lost packet indicator from the plot (default)")
    parser.add_argument('--hide-lost', action='store_false', help="hide the lost packet indicator from the plot")
    parser.set_defaults(plot_lost=True)

    args = parser.parse_args()

    assert 0 < args.loss_prob <= 1, "Loss probability must be between 0 and 1"

    # Simulated ACKs: (ACK_number, Time_of_arrival)
    ack_array = generate_ack_array(num_acks=args.num_acks, seed=args.seed, loss_prob=args.loss_prob)

    # Run simulation
    if args.use_cubic:
        tcp = TCPCubic(cwnd=args.cwnd, ssthresh=args.ssthresh)
        method_name = 'TCP CUBIC'

    elif args.use_reno:
        tcp = TCPReno(cwnd=args.cwnd, ssthresh=args.ssthresh)
        method_name = 'TCP Reno'

    elif args.use_aimd:
        tcp = TCPAIMD(cwnd=args.cwnd, ssthresh=args.ssthresh)
        method_name = 'TCP AIMD'

    else:
        raise NotImplementedError('Unknown congestion control method')

    print("{:15s} -> ssthresh: {}".format(method_name, args.ssthresh))

    # run simulation
    time_stamps, cwnd_values, loss_events, ssthreshs = \
        simulate(tcp, ack_array)

    # Plot results
    plt.figure(figsize=(10, 5))
    ax = plt.gca()

    if args.plot_lost:
        ax2 = plt.twinx()
        loss_data = [[x, y] for x, y, in zip(time_stamps, loss_events) if y == 1]
        lns1 = ax2.scatter(
            [x for x, _ in loss_data],
            [y for _, y in loss_data],
            marker='o', linestyle='-', label="Lost packet", color='red')
        # ax2.set_ylabel("Loss packet")
        ax2.get_yaxis().set_ticks([])

    lns2 = ax.plot(time_stamps, cwnd_values, marker='o' if args.plot_acks else None, linestyle='-', label="cwnd")
    if args.plot_ssthresh:
        lns3 = ax.plot(time_stamps, ssthreshs, label="ssthresh", color="green", alpha=0.7)
    ax.set_ylabel("Congestion Window (cwnd)")
    ax.set_xlabel("Time (s)")

    plt.title(f"{method_name} Congestion Control Simulation")
    plt.tight_layout()

    # lns2 and lsn3 are lists with only one line each
    lns = lns2
    if args.plot_ssthresh:
        lns += lns3
    if args.plot_lost:
        lns += [lns1, ]
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, loc=0)

    plt.grid()
    plt.show()
