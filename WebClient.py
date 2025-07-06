import socket


def send_request(host, port, path):
    # Create a client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to the server
        client_socket.connect((host, port))

        # Send an HTTP GET request
        request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\n\r\n"
        client_socket.sendall(request.encode("utf-8"))

        # Receive and print the response from the server
        response = client_socket.recv(1024).decode("utf-8")
        print(response)
    finally:
        # Close the client socket
        client_socket.close()


if __name__ == "__main__":
    # Set the server address, port, and path
    server_host = "127.0.0.1"
    server_port = 8000
    request_path = input("Please input the filename you want to get (.html)")

    # Send an HTTP GET request to the server
    send_request(server_host, server_port, request_path)
