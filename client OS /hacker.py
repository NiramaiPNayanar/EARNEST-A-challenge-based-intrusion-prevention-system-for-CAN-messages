
import socket
import struct
import time
import random


HOST = '192.x.x.x' #add your IP here , make sure both the server OS and the client OS have the same sub net
PORT = 12345
CLIENT_ID = "HACKER_001"  
CLIENT_TYPE = "DIAG"     
RETRY_DELAY = 1
MAX_RETRIES = 3

class MaliciousClient:
    def __init__(self):
        self.client_id = CLIENT_ID.ljust(10)[:10]
        self.retry_count = 0
        
    def send_malicious_request(self):
        for attempt in range(MAX_RETRIES):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
                    conn.settimeout(5.0)
                    conn.connect((HOST, PORT))
                    
                    conn.sendall(self.client_id.encode())
                    

                    conn.sendall(bytes([random.randint(1, 3)]))
                    

                    challenge = conn.recv(11)
                    if len(challenge) != 11:
                        print("Received incomplete challenge")
                        time.sleep(RETRY_DELAY)
                        continue
                        
 
                    bo_id = struct.unpack('!H', challenge[:2])[0]
                    challenge_type = challenge[2]
                    payload = list(challenge[3:])
                    
                    print(f"\nReceived challenge {challenge_type} (will fail)")
                    fake_response = bytes([random.randint(0, 255) for _ in range(8)])
                    conn.sendall(fake_response)
                    
                    result = conn.recv(7)
                    if result:
                        print(f"Server response: {result.decode()} (expected)")
                    return False
                    
            except (socket.error, struct.error) as e:
                print(f"Connection error: {e}")
                time.sleep(RETRY_DELAY * (self.retry_count + 1))
                self.retry_count += 1
        return False

if __name__ == "__main__":
    print("===== MALICIOUS CLIENT SIMULATION =====")
    print("This client doesn't know challenge responses and will always fail\n")
    
    attacker = MaliciousClient()
    success = attacker.send_malicious_request()
    print(f"\nAttack {'succeeded' if success else 'failed'} (always should fail)")


