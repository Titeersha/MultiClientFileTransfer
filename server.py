import socket
import threading
import hashlib
import os
import time

# Server settings
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

# Handle individual client sessions
def handle_client(client_socket, client_id):
    try:
        print(f"[SERVER] Handling client {client_id}")

        # Receive file name
        file_name = client_socket.recv(1024).decode().strip()
        if not file_name:
            print(f"[SERVER] Client {client_id} disconnected early.")
            return

        print(f"[SERVER] Receiving file {file_name} from client {client_id}")

        # Receive file data
        received_chunks = {}
        while True:
            header = client_socket.recv(6)  # Receive sequence number
            if not header:
                print(f"[SERVER] No more data from client {client_id}.")
                break

            if header == b"END\n":
                print(f"[SERVER] Received END signal from client {client_id}")
                break

            try:
                seq_num = int(header.decode().strip())
            except ValueError:
                print(f"[SERVER] Invalid header from client {client_id}: {header}")
                continue

            chunk = client_socket.recv(CHUNK_SIZE)
            if not chunk:
                break

            received_chunks[seq_num] = chunk
            print(f"[SERVER] Received chunk {seq_num} ({len(chunk)} bytes) from client {client_id}")

        print(f"[SERVER] Total received chunks from client {client_id}: {len(received_chunks)}")

        if not received_chunks:
            print(f"[SERVER] No file received from client {client_id}.")
            return

        # Reassemble the file
        output_file = f"received_{client_id}_{file_name}"
        with open(output_file, "wb") as f:
            for seq in sorted(received_chunks.keys()):
                f.write(received_chunks[seq])

        print(f"[SERVER] File {file_name} successfully received from client {client_id}")

        # Compute and send checksum
        checksum = calculate_checksum(output_file)
        print(f"[SERVER] Sending checksum {checksum} to client {client_id}")
        client_socket.sendall(checksum.encode() + b"\n")

        # Send the file back to the client
        send_file(client_socket, output_file, client_id)

    except Exception as e:
        print(f"[SERVER] Error with client {client_id}: {e}")
    finally:
        client_socket.close()
        print(f"[SERVER] Connection closed for client {client_id}")

# Function to send file chunks to client
def send_file(client_socket, file_path, client_id):
    print(f"[SERVER] Sending file {file_path} to client {client_id}")

    file_size = os.path.getsize(file_path)
    total_chunks = (file_size // CHUNK_SIZE) + (1 if file_size % CHUNK_SIZE else 0)

    with open(file_path, "rb") as f:
        for seq_num in range(total_chunks):
            chunk = f.read(CHUNK_SIZE)
            header = f"{seq_num:06d}".encode()

            client_socket.sendall(header + chunk)
            time.sleep(0.01)

    print(f"[SERVER] File sent successfully to client {client_id}")

# Start the multi-client server
def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"[SERVER] Listening on {HOST}:{PORT}...")

        client_id = 1
        while True:
            client_socket, addr = server_socket.accept()
            print(f"[SERVER] Connected to {addr}")

            thread = threading.Thread(target=handle_client, args=(client_socket, client_id))
            thread.start()
            client_id += 1

# Run the server
if __name__ == "__main__":
    start_server()
