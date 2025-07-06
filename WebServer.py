import socket
import os
import threading


def handle_request(tcp_socket):
    try:
        # 1. Receive request message from the client on connection socket
        request = tcp_socket.recv(1024).decode("utf-8")

        # 2. Extract the path of the requested object from the message
        request_lines = request.split("\r\n")
        first_line = request_lines[0].split(" ")
        uri = first_line[1]
        filename = uri[1:]  # Remove the leading "/"

        # 3. Read the corresponding file from disk
        if os.path.isfile(filename):
            with open(filename, "rb") as file:
                content = file.read()

            # 4. Determine the content type based on the file extension
            file_extension = os.path.splitext(filename)[1].lower()
            content_type = "text/html"  # Default content type for non-image files

            if file_extension in {".jpg", ".jpeg"}:
                content_type = "image/jpeg"
            elif file_extension == ".png":
                content_type = "image/png"
            elif file_extension == ".gif":
                content_type = "image/gif"

            # 5. Send the correct HTTP response with the appropriate content type
            response = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\n\r\n"
            response_binary = response.encode("utf-8") + content
            tcp_socket.sendall(response_binary)
        else:
            # 6. Send a 404 Not Found response for non-existing files
            response = "HTTP/1.1 404 Not Found\r\n\r\nFile Not Found"
            tcp_socket.sendall(response.encode("utf-8"))
    finally:
        # 7. Close the connection socket
        tcp_socket.close()


def start_server(server_address, server_port):
    # 1. Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 2. Bind the server socket to server address and server port
    server_socket.bind((server_address, server_port))

    # 3. Continuously listen for connections to server socket
    server_socket.listen(5)
    print(f"Server listening on http://{server_address}:{server_port}/")

    while True:
        # 4. When a connection is accepted, create a new thread to handle the request
        connection_socket, addr = server_socket.accept()
        print("Is connecting on :", addr)
        client_thread = threading.Thread(target=handle_request, args=(connection_socket,))
        client_thread.start()


if __name__ == "__main__":
    start_server("", int(input("Please input the port: ")))
