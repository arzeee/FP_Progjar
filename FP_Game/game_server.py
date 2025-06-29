import uuid
import json
import logging
from datetime import datetime

class GameServer:
    def __init__(self):
        self.players = {}

    def response(self, status="ERROR", message="", data=None):
        body = {
            "status": status,
            "message": message
        }
        if data:
            body.update(data)
        return (json.dumps(body) + "\r\n\r\n").encode()

    def proses(self, data):
        lines = data.strip().split()
        if not lines:
            return self.response("ERROR", "Empty command")

        cmd = lines[0]
        try:
            if cmd == "connect":
                return self.handle_connect()
            elif cmd == "set_location":
                return self.handle_set_location(lines)
            elif cmd == "get_all_players":
                return self.handle_get_all_players()
            elif cmd == "get_players_state":
                return self.handle_get_players_state()
            elif cmd == "attack":
                return self.handle_attack(lines)
            elif cmd == "disconnect":
                return self.handle_disconnect(lines)
            else:
                return self.response("ERROR", f"Unknown command: {cmd}")
        except Exception as e:
            return self.response("ERROR", str(e))

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
        return self.response("OK", "Connected", {"id": new_id})

    def handle_set_location(self, args):
        if len(args) < 4:
            return self.response("ERROR", "Usage: set_location <id> <x> <y> [attacking] [facing] [is_moving]")
        pid = args[1]
        if pid not in self.players:
            return self.response("ERROR", "Player not found")

        x = int(args[2])
        y = int(args[3])
        attacking = args[4] == "True" if len(args) > 4 else False
        facing = args[5] if len(args) > 5 else "right"
        is_moving = args[6] == "True" if len(args) > 6 else False

        self.players[pid].update({
            "x": x, "y": y,
            "attacking": attacking,
            "facing": facing,
            "is_moving": is_moving
        })
        return self.response("OK", "Location updated")

    def handle_get_all_players(self):
        return self.response("OK", "Player list", {"players": list(self.players.keys())})

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
        return self.response("OK", "Players state", {"players": state})

    def handle_attack(self, args):
        if len(args) < 6:
            return self.response("ERROR", "Usage: attack <attacker_id> <x> <y> <facing> <range>")
        attacker_id = args[1]
        if attacker_id not in self.players or self.players[attacker_id]["is_dead"]:
            return self.response("ERROR", "Invalid attacker")

        atk_x = int(args[2])
        atk_y = int(args[3])
        facing = args[4]
        atk_range = int(args[5])
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
        return self.response("OK", "Attack processed", {"hit": bool(hit_players), "hit_players": hit_players})

    def handle_disconnect(self, args):
        if len(args) < 2:
            return self.response("ERROR", "Usage: disconnect <id>")
        pid = args[1]
        if pid in self.players:
            del self.players[pid]
            return self.response("OK", "Player disconnected")
        else:
            return self.response("ERROR", "Player not found")
