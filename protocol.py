import struct
import socket
import time
import random
from email import header

from defines import *


class UDPBasedProtocol:
    def __init__(self, *, local_addr, remote_addr):
        self.udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.remote_addr = remote_addr
        self.udp_socket.bind(local_addr)

    def sendto(self, data):
        return self.udp_socket.sendto(data, self.remote_addr)

    def recvfrom(self, n):
        msg, addr = self.udp_socket.recvfrom(n)
        return msg

    def close(self):
        self.udp_socket.close()


class TCPPackage:
    def __init__(self, src_port, dest_port, seq, ack, data_offset=20, flags=0, window=8192, checksum=0,
                 urgent_pointer=0, data=b''):
        self.src_port = src_port
        self.dest_port = dest_port
        self.seq = seq
        self.ack = ack
        self.data_offset = data_offset
        self.flags = flags
        self.window = window
        self.checksum = checksum
        self.urgent_pointer = urgent_pointer
        self.data = data

    def pack(self):
        print("pack: ", self.src_port, self.dest_port, self.seq, self.ack, self.data_offset, self.flags, )
        header = struct.pack('!HHLLBBHHH',
                             self.src_port,
                             self.dest_port,
                             self.seq,
                             self.ack,
                             self.data_offset,
                             self.flags,
                             self.window,
                             self.checksum,
                             self.urgent_pointer)
        return header + self.data

    @classmethod
    def unpack(cls, msg):
        if len(msg) < HEADER_SIZE:
            return None

        header = msg[:HEADER_SIZE]
        data = msg[HEADER_SIZE:]

        fields = struct.unpack('!HHLLBBHHH', header)
        return cls(src_port=fields[0],
                   dest_port=fields[1],
                   seq=fields[2],
                   ack=fields[3],
                   data_offset=fields[4],
                   flags=fields[5],
                   window=fields[6],
                   checksum=fields[7],
                   urgent_pointer=fields[8],
                   data=data)


tcp_Package = TCPPackage(src_port=12345, dest_port=80, seq=1, ack=0, data='Зелибоба'.encode('utf-8'))
packed_data = tcp_Package.pack()
print("Пакет в байтах:", packed_data)

unpacked_Package = TCPPackage.unpack(packed_data)
print("Распакованный пакет:", vars(unpacked_Package))


class MyTCPProtocol(UDPBasedProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.src_port = self.remote_addr[1]
        self.dest_port = self.src_port

        # HANDSHAKE
        self.ack_start = 0
        self.seq_start = 0

        self.src_port = 2
        self.dest_port = 2

        self.send_bytes = 0  # packets send with confirmation
        self.received_bytes = 0  # packet came without confirmation

        self.window = 1000
        self.server_window = 1000

        self.is_connection_active = False

    '''
    def handshake(self):
        self.ack_start = random(0, LONG_MAX)

    def update_seq(self, window, package: TCPPackage):
        confirm_packs = package.ack - self.ack_start
        if confirm_packs < 0:
            confirm_packs += LONG_MAX

        if confirm_packs >= self.seq + self.window:
            return window

        if confirm_packs < self.seq:
            self.seq = self.seq_start + confirm_packs
            return self.window

    def wait_for_confirmation(self):
        for seconds in range(TIMEOUT):
            recv_package = TCPPackage.unpack(self.recvfrom(MAX_PACKAGE_SIZE))
            if recv_package is None:
                time.sleep(0.1)
            else:
                return recv_package

        raise TimeoutError

    def send_package(self, data: bytes):
        package = TCPPackage(src_port=self.remote_addr, dest_port=self.remote_addr, seq=self.seq + len(data), ack=self.ack,
                             data=data)
        return self.sendto(package.pack())

    def send(self, data: bytes):
        print("#        send called")
        windows_size = self.window
        package_id = 0
        package_count = (len(data) + MAX_DATA_SIZE - 1) // MAX_DATA_SIZE
        while package_id < package_count:
            if windows_size != 0:
                code = self.send_package(data[self.seq:(min(windows_size, MAX_DATA_SIZE, len(data)))])
                if code == -1:
                    print("#        connection error")
                    raise ConnectionError
                self.seq += code
                package_id += 1
                recv_package = TCPPackage.unpack(self.recvfrom(MAX_PACKAGE_SIZE))
            else:
                recv_package = self.wait_for_confirmation()
                windows_size = self.update_seq(window, recv_package)
                print("#        new window size:", windows_size)

            if recv_package is None:
                continue

        return self.sendto(data)
    '''

    '''
    def send_package(self, data: bytes):
        package = TCPPackage(src_port=self.src_port, dest_port=self.dest_port, seq=self.send_bytes,
                             ack=self.received_bytes,
                             data=data)
        return self.sendto(package.pack())

    def send_confirmation(self):
        package = TCPPackage(src_port=self.src_port, dest_port=self.dest_port, seq=self.send_bytes,
                             ack=self.received_bytes, flags=ACK)
        return self.sendto(package.pack())

    def wait_for_confirmation(self):
        for seconds in range(TIMEOUT):
            recv_package = TCPPackage.unpack(self.recvfrom(MAX_PACKAGE_SIZE))
            print("recv_package:", recv_package.seq, recv_package.ack, recv_package.flags)
            if recv_package is None:
                time.sleep(0.1)
            else:
                if (recv_package.flags & ACK) == ACK:
                    if recv_package.ack != self.send_bytes:
                        return recv_package.ack
        raise TimeoutError

    def send(self, data: bytes):
        packets_send = 0
        server_ack = -1
        while server_ack != self.send_bytes and packets_send != RESEND_LIMIT:
            code = self.send_package(data)
            packets_send += 1
            self.send_bytes += len(data)
            if code == -1:
                raise ConnectionError
            recv_package = TCPPackage.unpack(self.recvfrom(MAX_PACKAGE_SIZE))
            if recv_package is None:
                continue
            server_ack = recv_package.ack

        return len(data)

    def recv(self, n: int):
        print("recv func called")
        package = TCPPackage.unpack(self.recvfrom(n))
        if package is None:
            print("problem")
            return b''

        self.received_bytes += len(package.data)
        print("send conf")
        self.send_confirmation()
        return package.data
    '''

    def send_init_message(self):
        self.seq_start = random.randint(0, LONG_MAX)
        package = TCPPackage(src_port=self.src_port, dest_port=self.dest_port, seq=self.seq_start, ack=0, flags=SYN)
        self.sendto(package.pack())
        print("\nsend init_message\n")
        return 0

    def send_connection_confirm(self, package: TCPPackage):
        self.seq_start = package.ack
        self.ack_start = package.seq

        package = TCPPackage(src_port=self.src_port, dest_port=self.dest_port, seq=self.seq_start, ack=self.ack_start,
                             flags=ACK)
        self.sendto(package.pack())
        self.is_connection_active = True

    def answer_connection_query(self, package: TCPPackage):
        self.ack_start = package.seq + 1
        if self.ack_start > LONG_MAX:
            self.ack_start -= LONG_MAX
        self.seq_start = random.randint(0, LONG_MAX)

        self.src_port = package.src_port  # TODO
        self.dest_port = package.src_port

        answer = TCPPackage(src_port=self.src_port, dest_port=self.dest_port, seq=self.seq_start, ack=self.ack_start,
                            flags=SYN | ACK)

        self.sendto(answer.pack())
        return

    def send_package(self, data: bytes):
        package = TCPPackage(src_port=self.src_port, dest_port=self.dest_port, seq=self.send_bytes,
                             ack=self.received_bytes,
                             data=data)
        self.sendto(package.pack())
        return len(data)

    def handshake(self):
        self.send_init_message()
        header = self.wait_for_header()

        flags = ACK | SYN
        if header.flags & flags == flags:
            self.send_connection_confirm(header)
            return


        print("HANDSHAKE LAST PROBLEM")
        raise TypeError

    def get_last_pack(self):
        header = self.recvfrom(HEADER_SIZE)
        if header is None:
            return None

    def wait_for_header(self):
        print("\nwait for header\n")
        resend = 0
        header = TCPPackage.unpack(self.recvfrom(HEADER_SIZE))
        while header is None and resend != RESEND_LIMIT:
            print("\n resend \n")
            time.sleep(0.1)
            header = TCPPackage.unpack(self.recvfrom(HEADER_SIZE))
            resend += 1

        if resend == RESEND_LIMIT:
            raise ConnectionError
        print("\nheader get\n")
        return header

    def recv_connection(self):
        res_header = self.wait_for_header()

        print("\n recv connection")

        if res_header.flags & SYN == SYN:
            print("\n answe connection_query")
            self.answer_connection_query(res_header)

            end_header = self.wait_for_header()
            if end_header.flags & ACK == ACK:
                self.is_connection_active = True
                return

        print("HOLOQUEOST\n")
        raise ConnectionError

    def send(self, data: bytes):
        if not self.is_connection_active:
            self.handshake()
        print("\n\n\n    CONNECTION RECEIVED\n")

        self.send_bytes += len(data)
        if self.ack_start >= LONG_MAX:
            self.ack_start -= LONG_MAX

        package = TCPPackage(src_port=self.src_port, dest_port=self.dest_port, seq=self.send_bytes,
                             ack=self.received_bytes, data=data)
        self.sendto(package.pack())
        return len(data)

    def recv(self, n: int):
        if not self.is_connection_active:
            self.recv_connection()

            print("\n SEND CONNTECTION RECV")

        data = self.recvfrom(n + HEADER_SIZE)
        print("\n       received   data:  ", n + HEADER_SIZE, data , "   "    , data, '\n\n\n\n')
        package = TCPPackage.unpack(data)
        if package is None:
            return b''

        self.received_bytes += len(package.data)
        return package.data

    def close(self):
        super().close()
