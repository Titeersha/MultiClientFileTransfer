import socket
import hashlib
import os
import time

# Client settings
HOST = '127.0.0.1'
PORT = 12345
CHUNK_SIZE = 1024  # 1 KB per chunk

# Function to compute SHA256 checksum
def calculate_checksum(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)
    return hasher.hexdigest()

# Function to send file to the server
def send_file(client_socket, file_path):
    file_name = os.path.basename(file_path)
    print(f"[CLIENT] Sending filename {file_name} to server")
    client_socket.sendall(file_name.encode() + b"\n")
    time.sleep(1)  

    file_size = os.path.getsize(file_path)
    total_chunks = (file_size // CHUNK_SIZE) + (1 if file_size % CHUNK_SIZE else 0)

    print(f"[CLIENT] Uploading {file_name} ({total_chunks} chunks)")

    with open(file_path, "rb") as f:
        for seq_num in range(total_chunks):
            chunk = f.read(CHUNK_SIZE)
            header = f"{seq_num:06d}".encode()
            print(f"[CLIENT] Sending chunk {seq_num} ({len(chunk)} bytes)")
            client_socket.sendall(header + chunk)
            time.sleep(0.01)

    client_socket.sendall(b"END\n")
    print(f"[CLIENT] File upload completed. Waiting for response...")

# Function to receive file from the server
def receive_file(client_socket, received_file_name):
    received_chunks = {}

    print("[CLIENT] Waiting for checksum...")
    server_checksum = client_socket.recv(1024).decode().strip()
    print(f"[CLIENT] Received checksum {server_checksum}")

    while True:
        header = client_socket.recv(6)
        if not header:
            break

        try:
            seq_num = int(header.decode().strip())
        except ValueError:
            continue

        chunk = client_socket.recv(CHUNK_SIZE)
        received_chunks[seq_num] = chunk

    print("[CLIENT] Reassembling file...")

    with open(received_file_name, "wb") as f:
        for seq in sorted(received_chunks.keys()):
            f.write(received_chunks[seq])

    client_checksum = calculate_checksum(received_file_name)
    print(f"[CLIENT] Recalculated checksum {client_checksum}")

    if client_checksum == server_checksum:
        print("[CLIENT] File transfer successful! ✅")
    else:
        print("[CLIENT] File corrupted! ❌")

# Start the client process
def start_client(file_path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        print("[CLIENT] Connecting to server...")
        client_socket.connect((HOST, PORT))
        print(f"[CLIENT] Connected to {HOST}:{PORT}")

        send_file(client_socket, file_path)
        receive_file(client_socket, f"received_{file_path}")

        print("[CLIENT] Connection closed.")

# Run the client
if __name__ == "__main__":
    file_path = input("Enter file path to upload: ").strip()
    if os.path.exists(file_path):
        start_client(file_path)
    else:
        print("Error: File not found. Please enter a valid file path.")
