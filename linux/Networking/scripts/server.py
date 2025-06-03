# server.py
import socket
import time
import signal
import sys
from multiprocessing import Process

HOST = '0.0.0.0'  # Listen on all interfaces

def signal_handler(sig, frame):
    print('Signal received, server shutting down...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C

def handle_client(conn, addr):
    """
    Handles communication with a single client in a separate process.
    """
    print(f"Process {os.getpid()}: Connected by {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                print(f"Process {os.getpid()}: Client {addr} closed connection.")
                break
            print(f"Process {os.getpid()}: Received from {addr}: {data.decode()!r}")
            conn.sendall(b"Server acknowledges: " + data)
    except ConnectionResetError:
        print(f"Process {os.getpid()}: Connection reset by client {addr}.")
    except BrokenPipeError:
        print(f"Process {os.getpid()}: Broken pipe with client {addr}.")
    except Exception as e:
        print(f"Process {os.getpid()}: Error during communication with {addr}: {e}")
    finally:
        print(f"Process {os.getpid()}: Closing connection with {addr}")
        conn.close() # Ensure the connection is closed in the child process

if __name__ == "__main__":
    import os # Import os here for getpid()

    # Get port from command-line argument
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <port>")
        sys.exit(1)

    try:
        PORT = int(sys.argv[1])
        if not (1024 <= PORT <= 65535):
            raise ValueError("Port must be in range 1024–65535")
    except ValueError as e:
        print(f"Invalid port: {e}")
        sys.exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        print(f"Main process PID: {os.getpid()}")

        try:
            while True:
                conn, addr = s.accept()
                print(f"Main process: Accepted connection from {addr}. Spawning new process...")
                client_handler = Process(target=handle_client, args=(conn, addr))
                client_handler.daemon = True  # Allows the main process to exit even if children are still running
                client_handler.start()
                conn.close()  # Close the connection in the parent process; child has its own copy
        except KeyboardInterrupt:
            print("Server shutting down due to KeyboardInterrupt.")
        except Exception as e:
            print(f"An unexpected error occurred in the main server loop: {e}")
        finally:
            print("Server socket closed.")