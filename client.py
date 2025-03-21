#imports
import socket
import os
import time
import threading
import main
import queue

"""
This is the file sender class aka client class
The fields are:

server_ip: ip address of the server to send to
server_port: server port number
filename: the local file to send over the network
socket: the local socket to send from
sequence_number: keeps track of packet order
"""
class FileSender:
    """
    initialize the client class
    """
    def __init__(self, server_ip="127.0.0.1", server_port=6969, filename="file.txt"):
        self.server_ip = server_ip
        self.server_port = server_port
        self.filename = filename
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_ip, self.server_port))
        self.sequence_number = 0
        self.sent_packets = {}
        self.max_retries = 5
        self.timeout = 3
        self.ack_queue = queue.Queue()

    """
    sends the packet to the server
    """
    def send_packet(self, data_to_send):
        packet = main.PacketClass(self.sequence_number, data_to_send)
        self.socket.send(packet.packet_data.encode())
        self.sent_packets[self.sequence_number] = {'packet': packet, 'retries': 0}
        self.sequence_number += 1

    """
    enters a loop waiting to remove an ack from the queue and then calls receive ack when it is received
    """
    def receive_ack(self):
        while True:
            try:
                ack_seq = self.ack_queue.get(timeout=self.timeout)
                self.receive_ack_packet(ack_seq)
            except queue.Empty:
                self.timeout_retransmit()

    """
    prints out the ack number when received and removes it from the list of sent packets that weren't ACKed yet
    """
    def receive_ack_packet(self, ack_seq):
        if ack_seq in self.sent_packets:
            del self.sent_packets[ack_seq]
            print(f"ACK: {ack_seq}")

    """
    retransmits data if the amount of times the data has been retransmitted is not exceeded
    """
    def timeout_retransmit(self):
        for seq_num, data in list(self.sent_packets.items()):
            if data['retries'] < self.max_retries:
                print(f"Timeout occurred, retransmitting sequence: {seq_num}")
                self.sent_packets[seq_num]['retries'] += 1
                self.socket.send(data['packet'].packet_data.encode())

    """
    splits the file into packets and sends each of those packets using send_packet()
    """
    def send_file(self):
        with open(self.filename, "rb") as file:
            while True:
                file_data = file.read(1024)
                if not file_data:
                    break
                self.send_packet(file_data.decode())
                time.sleep(1)

        self.socket.close()

    """
    starts the client thread
    """
    def start(self):
        threading.Thread(target=self.receive_ack, daemon=True).start()
        self.send_file()

"""
runs the program
"""
if __name__ == "__main__":
    client = FileSender()
    client.start()