# === ship_proxy_client.py ===
import socket
import threading
import struct
from queue import Queue

LISTEN_PORT = 8080
OFFSHORE_HOST = 'offshore_proxy_server'
OFFSHORE_PORT = 9999

request_queue = Queue()

def debug(msg):
    print(f"[SHIP] {msg}")

def send_framed(conn, data):
    debug(f"Sending framed data of length: {len(data)}")
    conn.sendall(struct.pack('!I', len(data)) + data)

def recv_framed(conn):
    header = conn.recv(4)
    if not header:
        debug("Framed header missing")
        return None
    length = struct.unpack('!I', header)[0]
    debug(f"Receiving framed data of length: {length}")
    data = b''
    while len(data) < length:
        chunk = conn.recv(length - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def relay(src, dst, label):
    src.settimeout(30)
    try:
        while True:
            try:
                data = src.recv(4096)
                if not data:
                    debug(f"{label} connection closed.")
                    break
                debug(f"Relaying {len(data)} bytes from {label}")
                dst.sendall(data)
            except socket.timeout:
                debug(f"{label} timed out.")
                break
    except Exception as e:
        debug(f"Relay error ({label}): {e}")
    finally:
        try: src.shutdown(socket.SHUT_RD)
        except: pass
        try: dst.shutdown(socket.SHUT_WR)
        except: pass

def handle_client(client_sock):
    debug("Client connection enqueued")
    request_queue.put(client_sock)

def connect_offshore():
    debug("Connecting to offshore proxy...")
    conn = socket.create_connection((OFFSHORE_HOST, OFFSHORE_PORT))
    debug("Persistent connection established.")
    return conn

def forward_request_sequentially():
    offshore = connect_offshore()
    while True:
        client = request_queue.get()
        try:
            data = b""
            client.settimeout(2)
            while True:
                try:
                    chunk = client.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    if b"\r\n\r\n" in data:
                        break
                except socket.timeout:
                    break

            if not data:
                debug("Empty request from client")
                client.close()
                continue

            first_line = data.decode(errors='ignore').split('\r\n')[0]
            method = first_line.split()[0].upper()
            debug(f"Handling request: {first_line}")

            if method == "CONNECT":
                send_framed(offshore, data)
                resp = recv_framed(offshore)
                if not resp:
                    debug("Failed to receive tunnel confirmation")
                    raise Exception("Tunnel failed")
                client.sendall(resp)

                t1 = threading.Thread(target=relay, args=(client, offshore, "ship->offshore"), daemon=True)
                t2 = threading.Thread(target=relay, args=(offshore, client, "offshore->ship"), daemon=True)
                t1.start()
                t2.start()
                t1.join(timeout=30)
                t2.join(timeout=30)

                offshore.close()
                offshore = connect_offshore()
                debug("HTTPS tunnel closed. Reconnected offshore socket.")

            else:
                send_framed(offshore, data)
                resp = recv_framed(offshore)
                if not resp:
                    debug("Failed to receive HTTP response")
                    raise Exception("HTTP relay failed")
                client.sendall(resp)
                debug("HTTP response sent. Ready for next request.")

        except Exception as e:
            debug(f"Error: {e}")
            try:
                client.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            except:
                pass
        finally:
            client.close()
            debug("Client socket closed")

def accept_clients():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', LISTEN_PORT))
    server.listen()
    debug("Listening on port 8080")
    while True:
        conn, _ = server.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

if __name__ == '__main__':
    threading.Thread(target=forward_request_sequentially, daemon=True).start()
    accept_clients()
