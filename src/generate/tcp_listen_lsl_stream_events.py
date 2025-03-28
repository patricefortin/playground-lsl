import socket
from pylsl import StreamInfo, StreamOutlet, local_clock

# NOTE: this will handle only ONE client at a time
# You can use it with netcat:
#    nc localhost 8000 -v
# or
#    echo foo | nc localhost 8000 -v -q0

stream_name = "TcpListenStrStream"
stream_type = "TcpListenStr"

host = "0.0.0.0"
port = 8000

info = StreamInfo(stream_name, stream_type, 1, 0, 'string', f'tcp_listen_{port}')
outlet = StreamOutlet(info)

def handle_packet(data):
    msg = data.decode('utf-8').strip()
    outlet.push_sample([msg], local_clock())

print(f"Opening TCP {host}:{port}...")
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen()
print(f"Listening on TCP {host}:{port}...")

try:
    while True:
        # Accept a new connection
        connection, address = server_socket.accept()
        print(f"Connection established with {address}")
        
        try:
            # Receive data in chunks and handle each packet
            while True:
                data = connection.recv(1024)  # Adjust the size as necessary
                if not data:
                    # No data received, client closed the connection
                    break
                handle_packet(data)  # Call the function to process the packet
        finally:
            connection.close()  # Always close the connection when done
except:
    print("External try-except")
    server_socket.close()