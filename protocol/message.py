from protocol.message_types import MessageType
import struct

class Message:
    def __init__(self, msg_type: MessageType, payload: bytes = b""):
        self.msg_type = msg_type
        self.payload = payload

    def encode(self):
        # Message length(4 bytes) + Message Type(1 byte) + payload(varies)
        length = 1 + len(self.payload)
        return struct.pack(">IB", length, self.msg_type) + self.payload

    
    def decode(data: bytes):
        msg_type = MessageType(data[0])
        payload = data[1:]
        return Message(msg_type, payload)