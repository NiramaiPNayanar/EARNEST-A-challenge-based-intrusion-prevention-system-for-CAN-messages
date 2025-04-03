import socket
import struct
import time
from collections import OrderedDict

HOST = 'x.x.x.x' # add your Server OS IP address here
PORT = 12345
CLIENT_ID_PREFIX = "ECU"
RETRY_DELAY = 1
MAX_RETRIES = 3


PRIORITY_MAP = OrderedDict([
    ('ABS', 1),   
    ('RADIO', 2),
    ('DIAG', 3)     
])


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

class SecureCANClient:
    def __init__(self, client_type):
        self.client_type = client_type
        self.client_id = f"{CLIENT_ID_PREFIX}_{client_type}_001".ljust(10)[:10]
        self.retry_count = 0

    def send_challenge(self):
        for attempt in range(MAX_RETRIES):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
                    conn.settimeout(5.0)
                    conn.connect((HOST, PORT))
                    

                    conn.sendall(self.client_id.encode())
                    conn.sendall(bytes([PRIORITY_MAP[self.client_type]]))
                    

                    challenge = b''
                    while len(challenge) < 11:
                        chunk = conn.recv(11 - len(challenge))
                        if not chunk:
                            break
                        challenge += chunk

                    if len(challenge) != 11:
                        print("Invalid challenge size received!")
                        time.sleep(RETRY_DELAY)
                        continue
                        

                    bo_id = struct.unpack('!H', challenge[:2])[0]
                    challenge_type = challenge[2]
                    payload = list(challenge[3:11])
                    
                    print(f"\nReceived challenge {challenge_type} with payload {payload}")
                    

                    if 0 <= challenge_type < len(CHALLENGES):
                        response = CHALLENGES[challenge_type](payload.copy())
                        print(f"Computed response: {response}")
                        

                        response_bytes = bytes(response)
                        if len(response_bytes) != 8:
                            print(f"Error: Response length is {len(response_bytes)} bytes (should be 8)")
                            continue
                            
                        conn.sendall(response_bytes)
                        

                        result = conn.recv(7)
                        if result:
                            print(f"Server response: {result.decode()}")
                            return result.decode() == 'SUCCESS'
                    
            except (socket.error, struct.error) as e:
                print(f"Connection error: {e}")
                time.sleep(RETRY_DELAY * (self.retry_count + 1))
                self.retry_count += 1
        return False

if __name__ == "__main__":
    print("===== TESTING ALL CLIENT TYPES =====")
    

    for client_type, _ in sorted(PRIORITY_MAP.items(), key=lambda x: x[1]):
        print(f"\nTesting {client_type} client (priority {PRIORITY_MAP[client_type]})...")
        client = SecureCANClient(client_type)
        success = client.send_challenge()
        print(f"Challenge {'succeeded' if success else 'failed'}")


    print("\n===== LOCAL CHALLENGE VERIFICATION =====")
    test_payload = [i for i in range(8)]
    for i, challenge in enumerate(CHALLENGES):
        result = challenge(test_payload.copy())
        print(f"Challenge {i}: {result}")
