import uuid
import json
import logging
import os.path
from glob import glob
from datetime import datetime

class HttpServer:
    def __init__(self):
        self.players = {}
        self.types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.png': 'image/png',
            '.txt': 'text/plain',
            '.html': 'text/html',
        }

    def response(self, kode=404, message='Not Found', messagebody=bytes(), headers={}):
        tanggal = datetime.now().strftime('%c')
        resp = []
        resp.append("HTTP/1.0 {} {}\r\n" . format(kode,message))
        resp.append("Date: {}\r\n" . format(tanggal))
        resp.append("Connection: close\r\n")
        resp.append("Server: myserver/1.0\r\n")
        resp.append("Content-Length: {}\r\n" . format(len(messagebody)))
        for kk in headers:
            resp.append("{}:{}\r\n" . format(kk,headers[kk]))
        resp.append("\r\n")
        response_headers=''
        for i in resp:
            response_headers="{}{}" . format(response_headers,i)

        if (type(messagebody) is not bytes):
            messagebody = messagebody.encode()

        response = response_headers.encode() + messagebody
        
        return response

    def response_json(self, status="ERROR", message="", data=None):
        body = {"status": status, "message": message}
        if data:
            body.update(data)
        json_body = json.dumps(body)
        return self.response(200, 'OK', json_body, {"Content-Type": "application/json"})

    def proses(self, data):
        requests = data.split("\r\n")
        if not requests or len(requests[0].strip()) == 0:
            return self.response_json("ERROR", "Empty request")

        baris = requests[0]
        headers = [n for n in requests[1:] if n != '']
        j = baris.split(" ")
        try:
            method = j[0].upper().strip()
            object_address = j[1].strip()
            if method == 'GET':
                return self.http_get(object_address, headers)
            elif method == 'POST':
                return self.http_post(object_address, headers)
            else:
                return self.response(400, 'Bad Request', '', {})
        except IndexError:
            return self.response(400, 'Bad Request', '', {})

    def http_get(self, object_address, headers):
        if object_address == '/':
            return self.response(200, 'OK', 'Welcome to Samurai Arena', {'Content-Type': 'text/plain'})
        elif object_address == '/video':
            return self.response(302, 'Found', '', {'Location': 'https://youtu.be/katoxpnTf04'})
        elif object_address == '/santai':
            return self.response(200, 'OK', 'Santai dulu bos...', {'Content-Type': 'text/plain'})
        elif object_address == '/get_all_players':
            return self.handle_get_all_players()
        elif object_address == '/get_players_state':
            return self.handle_get_players_state()
        elif object_address == '/connect':
            return self.handle_connect()
        else:
            # File statis
            filepath = '.' + object_address
            if not os.path.isfile(filepath):
                return self.response(404, 'Not Found', 'File tidak ditemukan', {})
            with open(filepath, 'rb') as f:
                content = f.read()
            ext = os.path.splitext(filepath)[1]
            content_type = self.types.get(ext, 'application/octet-stream')
            return self.response(200, 'OK', content, {'Content-Type': content_type})

    def http_post(self, object_address, headers):
        parts = object_address.strip("/").split("/")
        if parts[0] == 'set_location' and len(parts) >= 4:
            return self.handle_set_location(parts)
        elif parts[0] == 'attack' and len(parts) >= 6:
            return self.handle_attack(parts)
        elif parts[0] == 'disconnect' and len(parts) >= 2:
            return self.handle_disconnect(parts)
        else:
            return self.response_json("ERROR", "Unknown POST endpoint or bad format")

    def handle_connect(self):
        new_id = str(uuid.uuid4())[:8]
        self.players[new_id] = {
            "x": 100, "y": 300,
            "attacking": False,
            "facing": "right",
            "is_moving": False,
            "hp": 100,
            "is_dead": False
        }
        logging.info(f"[CONNECT] New player: {new_id}")
        return self.response_json("OK", "Connected", {"id": new_id})

    def handle_set_location(self, parts):
        pid = parts[1]
        if pid not in self.players:
            return self.response_json("ERROR", "Player not found")

        x = int(parts[2])
        y = int(parts[3])
        attacking = parts[4] == "True" if len(parts) > 4 else False
        facing = parts[5] if len(parts) > 5 else "right"
        is_moving = parts[6] == "True" if len(parts) > 6 else False

        self.players[pid].update({
            "x": x, "y": y,
            "attacking": attacking,
            "facing": facing,
            "is_moving": is_moving
        })
        return self.response_json("OK", "Location updated")

    def handle_get_all_players(self):
        return self.response_json("OK", "Player list", {"players": list(self.players.keys())})

    def handle_get_players_state(self):
        state = {}
        for pid, p in self.players.items():
            state[pid] = {
                "x": p["x"],
                "y": p["y"],
                "hp": p["hp"],
                "is_dead": p["is_dead"],
                "facing": p["facing"],
                "is_moving": p["is_moving"],
                "attacking": p["attacking"]
            }
            p["attacking"] = False
        return self.response_json("OK", "Players state", {"players": state})

    def handle_attack(self, parts):
        attacker_id = parts[1]
        if attacker_id not in self.players or self.players[attacker_id]["is_dead"]:
            return self.response_json("ERROR", "Invalid attacker")

        atk_x = int(parts[2])
        atk_y = int(parts[3])
        facing = parts[4]
        atk_range = int(parts[5])
        hit_players = []

        for pid, target in self.players.items():
            if pid == attacker_id or target["is_dead"]:
                continue
            dx = target["x"] - atk_x
            dy = abs(target["y"] - atk_y)
            if dy < 50:
                if facing == "right" and 0 < dx <= atk_range:
                    target["hp"] -= 20
                    hit_players.append(pid)
                elif facing == "left" and -atk_range <= dx < 0:
                    target["hp"] -= 20
                    hit_players.append(pid)
                if target["hp"] <= 0:
                    target["hp"] = 0
                    target["is_dead"] = True
        return self.response_json("OK", "Attack processed", {"hit": bool(hit_players), "hit_players": hit_players})

    def handle_disconnect(self, parts):
        pid = parts[1]
        if pid in self.players:
            del self.players[pid]
            return self.response_json("OK", "Player disconnected")
        else:
            return self.response_json("ERROR", "Player not found")

