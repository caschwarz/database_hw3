#imports
import random
import time
import threading
import hashlib
import queue

"""
This is the class that represents a single packet
It has these fields:

sequence_number: the number that keeps tracks of what order this packet was supposed to be received
packet_data: the data contained in the packet
checksum: a md5 encoded checksum generated based on the contents of the packet
"""
class PacketClass:
    """
    Initialization function for the packet
    """
    def __init__(self, sequence_number, packet_data):
        self.sequence_number = sequence_number
        self.packet_data=packet_data
        self.checksum = self.calculate_checksum(packet_data)

    """
    this is the to string method for the packet class, used for printing the packet contents to standard output
    """
    def __str__(self):
        return "[Seq: "+str(self.sequence_number)+" Checksum: "+str(self.checksum)+" Contents: "+self.packet_data+"]"

    """
    This function creates a checksum based on the data contents in the packet using md5 encoding
    """
    def calculate_checksum(self, data):
        return hashlib.md5(data.encode()).hexdigest()

    """
    compared the calculated checksum before sending to the calculated checksum after sending to see if
    corruption occurred during sending
    """
    def is_corrupted(self):
        corrupted=self.calculate_checksum(self.packet_data) != self.checksum
        return corrupted

"""
This class represents the sender entity in the simulation
These are the fields contained:

networkSimulator: the network simulator class
max_retries: the max number of times to try sending the packet
timeout: the amount of time to wait before resending the packet
sequence_number: the sequence number that the sender is currently on
"""
class SenderClass:
    """
    Initialize the sender class
    """
    def __init__(self, networkSimulator, max_retries=5, timeout=3):
        self.networkSimulator = networkSimulator
        self.max_retries = max_retries
        self.timeout = timeout
        self.sequence_number = 0
        self.sent_packets = {}
        self.ack_queue = queue.Queue()

    """
    creates a packet out of the data to send and then sends the packet using the network simulator
    then increments the sequence number
    """
    def send_packet(self, data_to_send):
        packet = PacketClass(self.sequence_number, data_to_send)
        self.networkSimulator.send_to_network(packet)
        self.sent_packets[self.sequence_number] = {'packet': packet, 'retries': 0}
        self.sequence_number += 1

    """
    iterates through the list of sent packets and prints if it received an acknowledgement for the packet
    """
    def receive_ack(self, ack_seq):
        if ack_seq in self.sent_packets:
            del self.sent_packets[ack_seq]
            print("ACK: "+str(ack_seq))

    """
    continuously waits for an ack to be received in the ack queue and processes the ack in the
    above function if one is received
    """
    def handle_acknowledgement(self):
        while True:
            try:
                ack_seq = self.ack_queue.get(timeout=self.timeout)
                self.receive_ack(ack_seq)
            except queue.Empty:
                self.timeout_retransmit()

    """
    iterates through the list of sent packets and if that packet wasn't received and hasn't been retransmitted
    the max amount of times, resend it
    """
    def timeout_retransmit(self):
        for seqNum, data in list(self.sent_packets.items()):
            if data['retries'] < self.max_retries:
                message="timeout occurred, retransmitting sequence: "+str(seqNum)
                print(message)
                self.sent_packets[seqNum]['retries'] += 1
                self.networkSimulator.send_to_network(data['packet'])


    """
    begins the thread for the sender class, where it is continuously waiting for ACKs
    """
    def start_sender_thread(self):
        threading.Thread(target=self.handle_acknowledgement, daemon=True).start()

"""
This is the class for the receiver
It has these fields:

expected_seq_num: the number this receiver is expecting to receive on its next packet
"""
class Receiver:
    """
    initialize class
    """
    def __init__(self):
        self.expected_seq_num = 0

    """
    this function will receive the packet and based on the expected sequence number and if the packet is marked as 
    corrupted, it will print the status of that packet
    """
    def receive_packet(self, packet):
        if packet.is_corrupted():
            corrupt_msg="Packet "+str(packet.sequence_number)+" was corrupted"
            print(corrupt_msg)
            return None
        if packet.sequence_number == self.expected_seq_num:
            print(f"Received: {packet}")
            self.expected_seq_num += 1
            return packet.sequence_number
        elif packet.sequence_number > self.expected_seq_num:
            out_of_order="Out of order, expected number "+str(self.expected_seq_num)+", received number "+str(packet.sequence_number)
            print(out_of_order)
            return None
        else:
            duplicate_packet="duplicate packet "+str(packet.sequence_number)
            print(duplicate_packet)
            return packet.sequence_number

"""
network simulator class
it has the following fields:

loss_rate: chance of a packet being lost
corruption_rate: chance of a packet being corrupted
reorder_rate: chance of the packet being reordered
receiver: the receiver class
"""
class NetworkSimulatorClass:
    """
    initializes the network simulator class
    """
    def __init__(self, loss_rate=0.05, corruption_rate=0.05, reorder_rate=0.05):
        self.loss_rate = loss_rate
        self.corruption_rate = corruption_rate
        self.reorder_rate = reorder_rate
        self.receiver = Receiver()
        self.queue = queue.Queue()
        self.delay = 0.5

    """
    this function calculates if the packet will be reordered, corrupted or lost based on the provided
    rates for these errors
    """
    def send_to_network(self, packet):
        time.sleep(self.delay)
        if random.random() < self.loss_rate:
            print(f"Packet {packet.sequence_number} lost")
            return
        if random.random() < self.corruption_rate:
            print(f"Packet {packet.sequence_number} corrupted")
            packet.data = "corrupted :("
            packet.checksum = packet.calculate_checksum(packet.packet_data)
        if random.random() < self.reorder_rate:
            print(f"Reordering Packet {packet.sequence_number}")
            self.queue.put(packet)
        else:
            self.process_packet(packet)

    """
    takes the packet and passes it off to the receiver to analyze
    """
    def process_packet(self, packet):
        ack_seq = self.receiver.receive_packet(packet)
        if ack_seq is not None:
            self.queue.put(ack_seq)

    """
    puts the network simulator into its loop where it is listening for its queue to have packet in it
    """
    def start(self):
        while True:
            if not self.queue.empty():
                ack_seq = self.queue.get()
                sender.ack_queue.put(ack_seq)

"""
here is the main function that starts all of the classes and sends 10 packets of data
"""
if __name__ == "__main__":
    simulator = NetworkSimulatorClass(loss_rate=0.1, corruption_rate=0.1, reorder_rate=0.1)
    sender = SenderClass(simulator)
    sender.start_sender_thread()
    for i in range(10):
        sender.send_packet(f"message {i}")
        time.sleep(1)
    threading.Thread(target=simulator.start, daemon=True).start()
    while True:
        time.sleep(1)