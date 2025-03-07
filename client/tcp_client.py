import socket
import logging

def send_data_to_server(data, host='your_local_ip', port=65432):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(data.encode())
        response = s.recv(1024)
        logging.info(f"Received response: {response.decode()}")
        return response.decode()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    data = "Hello, Server!"
    response = send_data_to_server(data)
    # Update the online database with the response
    # Example: update_database(response)