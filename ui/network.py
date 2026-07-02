import socket
import threading
import zlib
import pickle
import json
import dataclasses
from enum import Enum

class NetworkEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        if isinstance(obj, Enum):
            return obj.name
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)

from scripts.combat_simulator import SimulationState, GameEnvironment, Combatant, MatrixAttributes

def decode_state(data: dict) -> SimulationState:
    env_data = data.get("environment", {})
    env = GameEnvironment(
        description=env_data.get("description", ""),
        modifiers=env_data.get("modifiers", {}),
        name=env_data.get("name", "Unknown"),
    )
    for k, v in env_data.items():
        setattr(env, k, v)

    state = SimulationState(environment=env)
    for k, v in data.items():
        if k != "environment" and k != "combatants":
            setattr(state, k, v)

    # Parse combatants
    for c_data in data.get("combatants", []):
        c = Combatant(name=c_data.get("name", "Unknown"), matrix=MatrixAttributes())
        for ck, cv in c_data.items():
            setattr(c, ck, cv)
        state.combatants.append(c)

    return state

class NetworkManager:
    def __init__(self, is_host: bool = False, host_ip: str = "127.0.0.1", port: int = 5555):
        self.is_host = is_host
        self.host_ip = host_ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []
        self.running = False
        self.latest_state_data = None
        self.app_callback = None

    def start(self, app_callback):
        self.app_callback = app_callback
        self.running = True
        if self.is_host:
            try:
                self.socket.bind(("0.0.0.0", self.port))
                self.socket.listen()
                threading.Thread(target=self._host_loop, daemon=True).start()
            except OSError:
                print(f"Port {self.port} already in use. Running host in disconnected mode.")
        else:
            try:
                self.socket.connect((self.host_ip, self.port))
                threading.Thread(target=self._client_loop, daemon=True).start()
            except Exception as e:
                print(f"Connection failed: {e}")

    def _host_loop(self):
        # We need a way to receive events back from clients too
        threading.Thread(target=self._host_receive_loop, daemon=True).start()

        while self.running:
            try:
                self.socket.settimeout(1.0)
                conn, addr = self.socket.accept()
                self.clients.append(conn)
                print(f"Client connected: {addr}")
                if self.latest_state_data:
                    self._send_to_conn(conn, self.latest_state_data)
            except socket.timeout:
                pass
            except Exception as e:
                pass

    def _host_receive_loop(self):
        # Extremely basic polling to receive action events from connected clients
        buffers = {}
        while self.running:
            for conn in self.clients.copy():
                try:
                    conn.setblocking(False)
                    data = conn.recv(1024)
                    if not data:
                        continue

                    if conn not in buffers:
                        buffers[conn] = b""
                    buffers[conn] += data

                    while b"<EVENT_END>" in buffers[conn]:
                        msg, buffers[conn] = buffers[conn].split(b"<EVENT_END>", 1)
                        event_data = json.loads(msg.decode('utf-8'))
                        if self.app_callback:
                            # Pass it as an action event
                            self.app_callback(None, {"action_event": event_data})
                except BlockingIOError:
                    pass
                except Exception as e:
                    pass
            import time
            time.sleep(0.05)

    def _client_loop(self):
        buffer = b""
        while self.running:
            try:
                self.socket.settimeout(1.0)
                data = self.socket.recv(8192)
                if not data:
                    break
                buffer += data

                while b"<END>" in buffer:
                    msg, buffer = buffer.split(b"<END>", 1)
                    try:
                        decompressed = zlib.decompress(msg).decode('utf-8')
                        payload = json.loads(decompressed)

                        if "state" in payload:
                            state_dict = payload["state"]
                            extra_data = payload.get("extra_data", {})
                        else:
                            state_dict = payload
                            extra_data = {}

                        decoded_state = decode_state(state_dict)

                        if self.app_callback:
                            self.app_callback(decoded_state, extra_data)
                    except Exception as e:
                        print(f"Deserialization error: {e}")

            except socket.timeout:
                pass
            except Exception as e:
                break

    def send_event(self, event_data: dict):
        if self.is_host:
            return

        try:
            serialized = json.dumps(event_data).encode('utf-8') + b"<EVENT_END>"
            self.socket.sendall(serialized)
        except Exception as e:
            print(f"Failed to send event: {e}")

    def broadcast_state(self, state_obj, extra_data=None):
        if not self.is_host:
            return

        try:
            payload = {
                "state": state_obj,
            }
            if extra_data:
                payload["extra_data"] = extra_data

            serialized = json.dumps(payload, cls=NetworkEncoder).encode('utf-8')
            compressed = zlib.compress(serialized) + b"<END>"
            self.latest_state_data = compressed

            for conn in self.clients.copy():
                try:
                    self._send_to_conn(conn, compressed)
                except:
                    self.clients.remove(conn)
        except Exception as e:
            pass

    def _send_to_conn(self, conn, data):
        conn.sendall(data)

    def stop(self):
        self.running = False
        try:
            self.socket.close()
        except:
            pass
