import socket
import time

class MeterSimulator:
    def __init__(self, port=4059):
        self.port = port
    
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.port))
        sock.listen(5)
        print(f"[Meter] Listening on port {self.port}")
        
        conn_count = 0
        while True:
            try:
                conn, addr = sock.accept()
                conn_count += 1
                tier = (conn_count % 20) // 5 + 1
                
                if tier == 1:
                    data = b'T1_' + b'X' * 95
                elif tier == 2:
                    data = b'T2_' + b'Y' * 295
                elif tier == 3:
                    data = b'T3_' + b'Z' * 1995
                else:
                    data = b'T4_' + b'A' * 15995
                
                print(f"[Meter #{conn_count}] Tier {tier} -> {len(data)}B")
                conn.sendall(data)
                conn.close()
                time.sleep(1)
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    MeterSimulator().run()
