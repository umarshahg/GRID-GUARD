"""
GRID GUARD — Module 4: FE-3
Docker Meter Emulator

Simulates a smart meter listening on TCP port 4059 (DLMS/COSEM).
Receives redirected traffic from FE-2 DNAT, logs it, and responds
with mock DLMS/COSEM frames.
"""

import socket
import logging
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [EMULATOR] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/emulator.log')
    ]
)
logger = logging.getLogger("MeterEmulator")

LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 4059
BUFFER_SIZE = 4096

def mock_dlms_response() -> bytes:
    """
    Return a mock DLMS/COSEM-like response frame.
    Real DLMS/COSEM is complex; this is a simple acknowledgment.
    """
    # HDLC frame: flag(0x7E) + address(0xA0) + control(0x13) + payload + FCS + flag(0x7E)
    mock_frame = b'\x7E\xA0\x13ACK\x7E'
    return mock_frame

def start_emulator():
    """Start the meter emulator server."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((LISTEN_IP, LISTEN_PORT))
        server_socket.listen(5)
        logger.info(f"Meter emulator listening on {LISTEN_IP}:{LISTEN_PORT}")
        
        while True:
            client_socket, client_addr = server_socket.accept()
            logger.info(f"Connection accepted from {client_addr}")
            
            try:
                # Receive data
                data = client_socket.recv(BUFFER_SIZE)
                if data:
                    logger.info(f"Received {len(data)} bytes from {client_addr}: {data[:50]}")
                    
                    # Send mock DLMS response
                    response = mock_dlms_response()
                    client_socket.sendall(response)
                    logger.info(f"Sent mock DLMS response to {client_addr}")
            except Exception as e:
                logger.error(f"Error handling client {client_addr}: {e}")
            finally:
                client_socket.close()
                logger.info(f"Connection closed with {client_addr}")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        server_socket.close()
        logger.info("Meter emulator stopped")

if __name__ == "__main__":
    logger.info("Starting GRID GUARD Module 4 - Meter Emulator (FE-3)")
    start_emulator()
