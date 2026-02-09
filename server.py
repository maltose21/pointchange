import http.server
import socketserver
import json
import sqlite3
import math
import uuid
import time
from urllib.parse import urlparse, parse_qs

PORT = 8000
DB_FILE = "rules.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rules (
                    rule_id TEXT PRIMARY KEY,
                    source_asset TEXT,
                    target_asset TEXT,
                    exchange_rate REAL,
                    step_size INTEGER,
                    min_amount INTEGER,
                    daily_limit INTEGER,
                    status TEXT,
                    description TEXT
                )''')
    
    # Seed data
    rules = [
        ("RULE_001", "MALL_POINT", "VIP_GROWTH", 0.1, 10, 10, 1000, "ENABLE", "10商城积分兑换1成长值"),
        ("RULE_002", "GAME_COIN", "COUPON", 0.05, 100, 100, 5000, "ENABLE", "100游戏币兑换5元优惠券"),
        ("RULE_003", "MALL_POINT", "GAME_COIN", 1.0, 1, 1, 10000, "ENABLE", "1商城积分兑换1游戏币"),
    ]
    
    for r in rules:
        try:
            c.execute("INSERT INTO rules VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", r)
        except sqlite3.IntegrityError:
            pass # Already exists
            
    conn.commit()
    conn.close()

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/v1/rules/query':
            self.handle_query_rules()
        else:
            # Serve static files for frontend
            super().do_GET()

    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/v1/rules/calculate':
            length = int(self.headers.get('Content-Length'))
            post_data = self.rfile.read(length)
            try:
                data = json.loads(post_data)
                self.handle_calculate(data)
            except json.JSONDecodeError:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
        else:
            self._set_headers(404)

    def handle_query_rules(self):
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM rules WHERE status='ENABLE'")
        rows = c.fetchall()
        rules = []
        for row in rows:
            rules.append(dict(row))
        conn.close()
        
        self._set_headers()
        self.wfile.write(json.dumps({"rules": rules}).encode())

    def handle_calculate(self, data):
        rule_id = data.get('rule_id')
        amount = data.get('amount')
        
        if not rule_id or amount is None:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Missing rule_id or amount"}).encode())
            return

        try:
            amount = int(amount)
        except ValueError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Amount must be an integer"}).encode())
            return

        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM rules WHERE rule_id=?", (rule_id,))
        rule = c.fetchone()
        conn.close()

        if not rule:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Rule not found"}).encode())
            return

        # Logic from PRD
        step_size = rule['step_size']
        min_amount = rule['min_amount']
        exchange_rate = rule['exchange_rate']

        if amount < min_amount:
            self._set_headers(400)
            self.wfile.write(json.dumps({
                "error": f"Amount {amount} is less than minimum {min_amount}",
                "min_amount": min_amount
            }).encode())
            return

        # Precision Strategy: Floor(Amount / Step) * Step
        valid_input = math.floor(amount / step_size) * step_size
        target_amount = valid_input * exchange_rate
        
        # In a real system, we might handle floating point precision more carefully (Decimal)
        # Here we just round to 2 decimal places for display
        target_amount = round(target_amount, 2)
        
        source_deduct_amount = valid_input
        remain_amount = amount - valid_input
        
        calc_token = str(uuid.uuid4())

        response = {
            "source_deduct_amount": source_deduct_amount,
            "target_grant_amount": target_amount,
            "remain_amount": remain_amount,
            "calc_token": calc_token,
            "message": "Calculation successful"
        }
        
        self._set_headers()
        self.wfile.write(json.dumps(response).encode())

if __name__ == "__main__":
    init_db()
    print(f"Starting server on port {PORT}...")
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        httpd.serve_forever()
