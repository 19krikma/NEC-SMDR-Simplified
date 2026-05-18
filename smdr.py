#!/usr/bin/python

import socket
import os
import sys
import errno
import re
import logging
import logging.config
import time
import yaml
import csv
from datetime import datetime
import threading

# Info
NAME = "NEC SMDR (Simplified)"
VERSION = "1.0"

# Settings
RECV = []
TS = []
STO = []
TYPE = []

SERVERS = {}

pattern = re.compile(
    r"^(\w{3,})\s+(\d{2}:\d{2})\s+(\d{2}/\d{2})\s+(\d{3})\s+(\d{2}:\d{2}:\d{2})?\s+(\d{3,})\s+(\d+)\s+([^\r\S]*[\w\d.,'&\- ]*\S)?\s+(.+?)$"
)


def config_reader():
    global SERVERS
    with open("config.yaml") as file:
        cfg = yaml.safe_load(file)

    RECV.append(cfg.get("RECV", 1024))
    TS.append(cfg.get("TS", 5))
    STO.append(cfg.get("STO", 5))

    for x in cfg.get("DATA", []):
        TYPE.append(x)
    for x in cfg.get("ALERT", []):
        TYPE.append(str(x))

    for server in cfg.get("SERVERS", []):
        name = server.get("name")
        if name:
            SERVERS[name] = {
                "name": name,
                "host": server.get("host"),
                "port": server.get("port")
            }


def get_server(name: str, field: str = None):
    if name not in SERVERS:
        raise KeyError(f"Server '{name}' not found in configuration.")
    if field:
        field = field.lower()
        if field not in SERVERS[name]:
            raise KeyError(f"Field '{field}' not found for server '{name}'.")
        return SERVERS[name][field]
    return SERVERS[name]


class SMDRWorker:
    def __init__(self, sysname, syshost, sysport):
        self.name = sysname
        self.host = syshost
        self.port = sysport
        self.setup_logging()
        self.logger.info(f"Created Session")
        self.run()

    def setup_logging(self):
        # Create server-specific directory if it doesn't exist
        os.makedirs(self.name, exist_ok=True)

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

        # File handler in same folder as CSV
        file_path = os.path.join(self.name, f"{datetime.now():%Y-%m-%d}.log")
        file_handler = logging.FileHandler(file_path, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(console_formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def run(self):
        while True:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.logger.info(f"SMDR CONNECTING {self.host}:{self.port}")
                self.sock.connect((self.host, self.port))
                self.logger.info(f"SMDR CONNECTED {self.host}:{self.port}")
                self.sock.settimeout(STO[0])

                while True:
                    try:
                        if self.sock_check():
                            break
                        self.data = self.sock.recv(RECV[0])
                        if self.data:
                            self.data_handler()
                    except socket.timeout:
                        self.logger.info(f"No Data Received, Killing Session {self.name}")
                        break
                    except OSError as e:
                        # Handle all socket-related OSErrors
                        if e.errno in (errno.ECONNREFUSED, errno.ECONNRESET, errno.ECONNABORTED,
                                       errno.ETIMEDOUT, errno.ENETUNREACH, errno.EHOSTUNREACH,
                                       errno.EADDRNOTAVAIL):
                            self.logger.error(f"Socket error ({e.errno}): {e.strerror}")
                        else:
                            self.logger.error(f"Unexpected socket error: {e}")
                        break
            except socket.timeout:
                self.logger.error(f"Connection attempt timed out for {self.host}:{self.port}")
            except socket.gaierror:
                self.logger.error(f"Hostname could not be resolved: {self.host}")
            except ConnectionRefusedError:
                self.logger.error(f"Connection refused by server: {self.host}:{self.port}")
            except ConnectionResetError:
                self.logger.error(f"Connection was reset by peer: {self.host}:{self.port}")
            except ConnectionAbortedError:
                self.logger.error(f"Connection aborted: {self.host}:{self.port}")
            except OSError as e:
                # Top-level connection OSError
                if e.errno in (errno.ECONNREFUSED, errno.ECONNRESET, errno.ECONNABORTED,
                               errno.ETIMEDOUT, errno.ENETUNREACH, errno.EHOSTUNREACH,
                               errno.EADDRNOTAVAIL):
                    self.logger.error(f"Connection error ({e.errno}): {e.strerror}")
                else:
                    self.logger.error(f"Unexpected OSError: {e}")
            finally:
                self.sock.close()
                self.logger.info(f"DISCONNECTING FROM {self.host}:{self.port}")
                break
        self.logger.info(f"Session END")


    def data_handler(self):
        self.logger.info(f"RAW DATA: {self.data}")
        text_data = self.data.decode("utf-8")
        if not self.page_detect(text_data):
            self.logger.info(f"Page Found (Unknown Type): {text_data[:50]}")
            return
        
        matches = pattern.finditer(text_data)
        for match in matches:
            store = [
                match.group(1),
                match.group(2),
                match.group(3),
                match.group(4),
                match.group(5) or "",
                match.group(6),
                match.group(7),
                match.group(8) or "",
            ]
            self.data_csv(self.name, store)

    def data_csv(self, directory, data):
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, f"{datetime.now():%Y-%m-%d}.csv")
        file_is_new = not os.path.exists(filepath) or os.path.getsize(filepath) == 0

        with open(filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if file_is_new:
                writer.writerow([
                    "Type", "Time", "Date", "Trunk", "Duration",
                    "EXT/TRUNK", "Number", "Additional Info"
                ])
            writer.writerow(data)

    def page_detect(self, text: str) -> bool:
        for t in TYPE:
            if t == text[:4].strip():
                return True
        return False

    def sock_check(self) -> bool:
        try:
            self.sock.send(b"\n")
            return False
        except socket.error:
            return True


if __name__ == "__main__":
    config_reader()
    print(SERVERS)
    for server_name, info in SERVERS.items():
        threading.Thread(
            target=SMDRWorker,
            args=(info['name'], info['host'], info['port']),
            name=server_name
        ).start()
        time.sleep(2)
