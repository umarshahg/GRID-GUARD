import socket
import time
import random
import struct

class MeterSimulator:
    def __init__(self, port=4059):
        self.port = port
        self.mode_cycle = 0
    
    def tier1_normal(self):
        """Tier 1 (5-35%): Normal consumption"""
        return struct.pack('!I', random.randint(50, 100))
    
    def tier2_suspicious(self):
        """Tier 2 (40-80%): Unusual pattern - slightly increased"""
        return struct.pack('!I', random.randint(200, 350))
    
    def tier3_anomaly(self):
        """Tier 3 (80-95%): Rapid requests - many packets"""
        return b''.join([struct.pack('!I', random.randint(400, 500)) for _ in range(5)])
    
    def tier4_attack(self):
        """Tier 4 (95-100%): Attack pattern - massive rapid requests"""
        return b''.join([struct.pack('!I', random.randint(800, 1000)) for _ in range(20)])
    
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.port))
        sock.listen(5)
        print(f"[Meter] Listening on port {self.port}")
        
        while True:
            try:
                conn, addr = sock.accept()
                
                # Cycle through all tiers
                self.mode_cycle = (self.mode_cycle + 1) % 40
                
                if self.mode_cycle < 10:
                    # Tier 1: Normal (5-35%)
                    data = self.tier1_normal()
                    tier = "Tier 1 (Normal)"
                elif self.mode_cycle < 20:
                    # Tier 2: Suspicious (40-80%)
                    data = self.tier2_suspicious()
                    tier = "Tier 2 (Suspicious)"
                elif self.mode_cycle < 30:
                    # Tier 3: Anomaly (80-95%)
                    data = self.tier3_anomaly()
                    tier = "Tier 3 (Anomaly)"
                else:
                    # Tier 4: Attack (95-100%)
                    data = self.tier4_attack()
                    tier = "Tier 4 (Attack)"
                
                print(f"[Meter] {tier} - Sent {len(data)} bytes")
                conn.send(data)
                conn.close()
                time.sleep(1)
            except Exception as e:
                print(f"[Meter] Error: {e}")

if __name__ == "__main__":
    meter = MeterSimulator()
    meter.run()
