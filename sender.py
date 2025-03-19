#imports
import struct

"""
This packet class represents a single data packet sent over UDP.
It has the following fields:

sequence_number: the unique number associated with this packet
packet_data: the data given in this packet
checksum: a checksum calculated based on the packets contents
"""
class packet:

    """
    initialization function for the packet class
    """
    def __init__(self, sequence_number, packet_data, checksum):
        self.sequence_number=sequence_number
        self.packet_data=packet_data
        self.checksum=self.calculate_checksum()

    """
    checksum generation function
    this function converts the packet data to binary and adds up all of the byte data
    then we mod the checksum by 64 so it doesn't get too large
    """
    def calculate_checksum(self):
        data=self.packet_data
        byte_data=bytearray(data, 'utf-8')
        checksum_val=sum(byte_data)%64
        return checksum_val

    """
    this function takes the data in the packet including the sequence number, packet data and checksum
    and converts it into binary format
    """
    def convert_to_bytes(self):
        sequence_number_bits=struct.pack("I", self.sequence_number)
        checksum_bits=struct.pack("B", self.checksum)
        packet_data_bits=self.packet_data.encode()
        return sequence_number_bits + checksum_bits + packet_data_bits