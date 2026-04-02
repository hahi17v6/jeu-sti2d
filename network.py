import socket
import threading
import json

class NetworkManager:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.01) # Non-blocking
        self.is_server = False
        self.is_connected = False
        self.remote_addr = None
        self.my_port = 5555
        self.remote_port = 5555
        
        self.last_received_data = None
        
    def host(self):
        try:
            self.socket.bind(('', self.my_port))
            self.is_server = True
            print(f"Hosting on port {self.my_port}...")
        except Exception as e:
            print(f"Host error: {e}")

    def connect(self, ip):
        self.remote_addr = (ip, self.remote_port)
        self.is_server = False
        self.is_connected = True
        print(f"Connecting to {ip}:{self.remote_port}...")

    def send_input(self, input_dict):
        if not self.is_connected and not self.is_server:
            return
            
        if self.is_server and not self.remote_addr:
            # Wait for client to send something first
            return
            
        try:
            data = json.dumps(input_dict).encode('utf-8')
            if self.remote_addr:
                self.socket.sendto(data, self.remote_addr)
        except:
            pass

    def receive_input(self):
        try:
            data, addr = self.socket.recvfrom(1024)
            if self.is_server:
                self.remote_addr = addr
                self.is_connected = True
            
            self.last_received_data = json.loads(data.decode('utf-8'))
            return self.last_received_data
        except:
            return None
