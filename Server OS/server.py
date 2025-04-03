import socket
import random
import struct
import threading
from queue import PriorityQueue


HOST = '0.0.0.0'
PORT = 12345


PRIORITY_MAP = {
    'ABS': 1,
    'RADIO': 2,
    'DIAG': 3
}


def sum_to_fifth(payload):
    if len(payload) > 4:
        payload = payload.copy()
        payload[4] = (payload[4] + 1) % 256
    return payload

def reverse_it(payload):
    return payload[::-1]

def switch_first_last(payload):
    if len(payload) > 1:
        payload = payload.copy()
        payload[0], payload[-1] = payload[-1], payload[0]
    return payload

def rotate_right(payload):
    return payload[-3:] + payload[:-3]

def zero_even(payload):
    return [0 if i%2==0 else v for i,v in enumerate(payload)]

def zero_odd(payload):
    return [v if i%2==0 else 0 for i,v in enumerate(payload)]

def full_f(payload):
    return payload[:2] + [0xF]*(len(payload)-2)

def full_z(payload):
    return [payload[0]] + [0]*(len(payload)-2) + [payload[-1]]

def middle_f(payload):
    half = len(payload)//2
    return [0xF]*half + payload[half:]

def odd_even_switch(payload):
    if len(payload)%2 == 0:
        result = []
        for i in range(0, len(payload)-1, 2):
            result.extend([payload[i+1], payload[i]])
        return result
    return payload

CHALLENGES = [
    sum_to_fifth, reverse_it, switch_first_last, rotate_right,
    zero_even, zero_odd, full_f, full_z, middle_f, odd_even_switch
]

class DBCSimulator:
    def __init__(self):
        self.message_map = {}
        
    def generate_frame(self, bo_id):
        return [random.randint(0, 255) for _ in range(8)]

priority_queue = PriorityQueue()
dbc = DBCSimulator()

def handle_client(conn, addr):
    try:
        conn.settimeout(5.0)
        

        client_id = b''
        while len(client_id) < 10:
            chunk = conn.recv(10 - len(client_id))
            if not chunk:
                return
            client_id += chunk
            
        print(f"\nClient connected: {client_id.decode()} from {addr}")


        bo_id = random.randint(0, 4095)
        challenge_type = random.randint(0, len(CHALLENGES)-1)
        payload = dbc.generate_frame(bo_id)


        challenge_msg = struct.pack('!HB8B', bo_id, challenge_type, *payload)
        conn.sendall(challenge_msg)


        response = b''
        while len(response) < 8:
            chunk = conn.recv(8 - len(response))
            if not chunk:
                break
            response += chunk

        if len(response) != 8:
            print("Incomplete response received")
            conn.sendall(b'FAILED')
            return
            
        expected_result = CHALLENGES[challenge_type](payload.copy())
        client_result = list(response)
        
        if client_result == expected_result:
            conn.sendall(b'SUCCESS')
            print(f"Challenge {challenge_type} SUCCESS")
            print(f"Payload:   {payload}")
            print(f"Expected:  {expected_result}")
            print(f"Received:  {client_result}")
        else:
            conn.sendall(b'FAILED')
            print(f"Challenge {challenge_type} FAILED")
            print(f"Payload:   {payload}")
            print(f"Expected:  {expected_result}")
            print(f"Received:  {client_result}")
            
    except Exception as e:
        print(f"Error with {addr}: {e}")
    finally:
        conn.close()

def process_queue():
    while True:
        priority, conn, addr = priority_queue.get()
        handle_client(conn, addr)
        priority_queue.task_done()

threading.Thread(target=process_queue, daemon=True).start()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server listening on {HOST}:{PORT}")
    
    try:
        while True:
            conn, addr = server.accept()
            priority_byte = conn.recv(1)
            if priority_byte:
                priority = int(priority_byte[0])
                priority_queue.put((priority, conn, addr))
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
