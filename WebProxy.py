import socket
import threading


class WebProxy:
    def __init__(self, proxy_port):
        self.proxy_port = proxy_port

    def handle_proxy_request(self, client_socket):
        try:
            # Receive request message from the client
            request = client_socket.recv(4096).decode("utf-8")

            # Extract the destination host and port from the request
            destination_host, destination_port = self.extract_destination(request)

            # Forward the request to the destination server
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((destination_host, destination_port))
            server_socket.sendall(request.encode("utf-8"))

            # Receive and forward the response from the destination server
            while True:
                response = server_socket.recv(4096)
                if not response:
                    break  # Break the loop if no more data is received
                client_socket.sendall(response)

        except Exception as e:
            print(f"Error handling proxy request: {e}")
        finally:
            # Close the sockets
            client_socket.close()
            server_socket.close()

    def extract_destination(self, request):
        # Extract the destination host and port from the request
        lines = request.split("\r\n")
        first_line = lines[0].split(" ")
        uri = first_line[1]

        # Assume the URI format is http://host:port/path
        parts = uri.split("/")
        host_port = parts[2].split(":") if ":" in parts[2] else [parts[2], 80]

        destination_host = host_port[0]
        destination_port = int(host_port[1])

        return destination_host, destination_port

    def start_proxy(self):
        # Create a proxy server socket
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_socket.bind(("", self.proxy_port))
        proxy_socket.listen(5)
        print(f"Proxy server listening on port {self.proxy_port}")

        while True:
            # Accept a client connection
            client_socket, _ = proxy_socket.accept()

            # Create a new thread to handle the proxy request
            proxy_thread = threading.Thread(target=self.handle_proxy_request, args=(client_socket,))
            proxy_thread.start()


if __name__ == "__main__":
    proxy_port = int(input("Please input the proxy port: "))
    web_proxy = WebProxy(proxy_port)
    web_proxy.start_proxy()
