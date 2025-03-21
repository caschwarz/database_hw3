#imports
import socket
import threading
import os
import main

"""
this is the file receiver class with the following attributes:

port: the port it listens on
file_name: the file that it writes the contents received to
server_socket: the socket that receives the file
"""
class FileReceiver:
    """
    initialization function
    """
    def __init__(self, port=6969, filename="received_file.txt"):
        self.port = port
        self.filename = filename
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("0.0.0.0", self.port))
        self.server_socket.listen(1)
        self.expected_seq_num = 0

    """
    receives the file and then writes a new file on the local computer
    """
    def handle_client(self, client_socket):
        with open(self.filename, "wb") as file:
            while True:
                packet_data = client_socket.recv(1024)
                if not packet_data:
                    break
                packet = main.PacketClass(self.expected_seq_num, packet_data.decode())
                ack_seq = self.receive_packet(packet)
                if ack_seq is not None:
                    client_socket.send(str(ack_seq).encode())
                    file.write(packet_data)
                    self.expected_seq_num += 1
        client_socket.close()

    """
    prints out the status of the packets of the file that it is receiving
    """
    def receive_packet(self, packet):
        if packet.is_corrupted():
            print(f"Packet {packet.sequence_number} was corrupted")
            return None
        if packet.sequence_number == self.expected_seq_num:
            print(f"Received: {packet}")
            return packet.sequence_number
        elif packet.sequence_number > self.expected_seq_num:
            print(f"Out of order, expected {self.expected_seq_num}, received {packet.sequence_number}")
            return None
        else:
            print(f"Duplicate packet {packet.sequence_number}")
            return packet.sequence_number

    """
    starts the server thread, which waits to receive a file from the client
    """
    def start(self):
        print(f"Server started on port {self.port}")
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

"""
runs the program when it starts
"""
if __name__ == "__main__":
    server = FileReceiver()
    server.start()