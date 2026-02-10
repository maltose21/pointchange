import http.server
import socketserver
import json
import sqlite3
import math
import uuid
import time
import datetime
from urllib.parse import urlparse, parse_qs

PORT = 8000
DB_FILE = "rules.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Assets Table (New)
    c.execute('''CREATE TABLE IF NOT EXISTS assets (
                    asset_code TEXT PRIMARY KEY,
                    asset_name TEXT,
                    service_url TEXT,
                    deduct_api TEXT,
                    grant_api TEXT,
                    query_api TEXT,
                    auth_token TEXT,
                    description TEXT,
                    updated_at TEXT
                )''')

    # 2. Rules Table (Existing)
    c.execute('''CREATE TABLE IF NOT EXISTS rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT,
                    source_asset TEXT,
                    target_asset TEXT,
                    exchange_rate REAL,
                    step_size INTEGER,
                    min_amount INTEGER,
                    daily_limit INTEGER,
                    status TEXT,
                    updated_by TEXT,
                    updated_at TEXT
                )''')
    
    # Seed Assets if empty
    c.execute("SELECT count(*) FROM assets")
    if c.fetchone()[0] == 0:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        assets = [
            ("MALL_POINT", "商城积分", "http://mall-service.local", "/api/point/deduct", "/api/point/grant", "/api/point/balance", "sk_mall_123", "核心商城购物积分", now),
            ("GAME_COIN", "游戏币", "http://game-service.local", "/v1/coin/sub", "/v1/coin/add", "/v1/coin/get", "sk_game_456", "娱乐中心通用货币", now),
            ("VIP_GROWTH", "会员成长值", "http://member-service.local", "", "/api/growth/add", "/api/growth/get", "sk_vip_789", "用户等级成长值(只增不减)", now),
            ("COUPON", "优惠券", "http://promo-service.local", "", "/api/coupon/issue", "", "sk_promo_000", "通用现金抵扣券", now)
        ]
        for a in assets:
            c.execute("INSERT INTO assets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", a)

    # Seed Rules if empty (Ensure they match asset codes)
    c.execute("SELECT count(*) FROM rules")
    if c.fetchone()[0] == 0:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rules = [
            ("R_001", "商城积分兑换成长值", "MALL_POINT", "VIP_GROWTH", 0.1, 10, 10, 1000, "ENABLE", "admin", now),
            ("R_002", "游戏币兑换优惠券", "GAME_COIN", "COUPON", 0.05, 100, 100, 5000, "ENABLE", "wangfengxi1", now),
        ]
        for r in rules:
            c.execute("INSERT INTO rules VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", r)
            
    conn.commit()
    conn.close()

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/v1/admin/rules':
            self.handle_list_rules(parsed_path.query)
        elif parsed_path.path == '/api/v1/admin/assets':
            self.handle_list_assets()
        else:
            super().do_GET()

    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/v1/admin/rules':
            self.handle_create_rule()
        elif parsed_path.path == '/api/v1/admin/assets':
            self.handle_create_asset()
        elif parsed_path.path == '/api/v1/rules/calculate':
            # Demo calc logic could be updated to return API info
            pass
        else:
            self._set_headers(404)

    def do_PUT(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path.startswith('/api/v1/admin/rules/'):
            rule_id = parsed_path.path.split('/')[-1]
            self.handle_update_rule(rule_id)
        elif parsed_path.path.startswith('/api/v1/admin/assets/'):
            asset_code = parsed_path.path.split('/')[-1]
            self.handle_update_asset(asset_code)
        else:
            self._set_headers(404)

    def do_DELETE(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path.startswith('/api/v1/admin/rules/'):
            rule_id = parsed_path.path.split('/')[-1]
            self.handle_delete_rule(rule_id)
        elif parsed_path.path.startswith('/api/v1/admin/assets/'):
            asset_code = parsed_path.path.split('/')[-1]
            self.handle_delete_asset(asset_code)
        else:
            self._set_headers(404)

    # --- Asset Handlers ---
    def handle_list_assets(self):
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM assets ORDER BY updated_at DESC")
        rows = c.fetchall()
        assets = [dict(row) for row in rows]
        conn.close()
        self._set_headers()
        self.wfile.write(json.dumps({"items": assets}).encode())

    def handle_create_asset(self):
        length = int(self.headers.get('Content-Length'))
        data = json.loads(self.rfile.read(length))
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute("""INSERT INTO assets (asset_code, asset_name, service_url, deduct_api, grant_api, query_api, auth_token, description, updated_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (data['asset_code'], data['asset_name'], data['service_url'], 
                       data['deduct_api'], data['grant_api'], data['query_api'], 
                       data['auth_token'], data['description'], now))
            conn.commit()
            self._set_headers(201)
            self.wfile.write(json.dumps({"message": "Asset Created"}).encode())
        except sqlite3.IntegrityError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Asset Code already exists"}).encode())
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())
        finally:
            conn.close()

    def handle_update_asset(self, asset_code):
        length = int(self.headers.get('Content-Length'))
        data = json.loads(self.rfile.read(length))
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute("""UPDATE assets SET 
                         asset_name=?, service_url=?, deduct_api=?, grant_api=?, 
                         query_api=?, auth_token=?, description=?, updated_at=?
                         WHERE asset_code=?""",
                      (data['asset_name'], data['service_url'], data['deduct_api'], 
                       data['grant_api'], data['query_api'], data['auth_token'], 
                       data['description'], now, asset_code))
            conn.commit()
            self._set_headers(200)
            self.wfile.write(json.dumps({"message": "Asset Updated"}).encode())
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())
        finally:
            conn.close()

    def handle_delete_asset(self, asset_code):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            # Check if used in rules
            c.execute("SELECT count(*) FROM rules WHERE source_asset=? OR target_asset=?", (asset_code, asset_code))
            if c.fetchone()[0] > 0:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Cannot delete asset currently used in rules"}).encode())
                return

            c.execute("DELETE FROM assets WHERE asset_code=?", (asset_code,))
            conn.commit()
            self._set_headers(200)
            self.wfile.write(json.dumps({"message": "Asset Deleted"}).encode())
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())
        finally:
            conn.close()

    # --- Rule Handlers (Existing) ---
    def handle_list_rules(self, query_string):
        params = parse_qs(query_string)
        page = int(params.get('page', [1])[0])
        page_size = int(params.get('page_size', [10])[0])
        offset = (page - 1) * page_size
        status = params.get('status', [None])[0]
        
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        sql = "SELECT * FROM rules WHERE 1=1"
        args = []
        if status and status != 'ALL':
            sql += " AND status = ?"
            args.append(status)
            
        count_sql = "SELECT count(*) FROM (" + sql + ")"
        c.execute(count_sql, args)
        total = c.fetchone()[0]
        
        sql += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        args.extend([page_size, offset])
        c.execute(sql, args)
        
        rows = c.fetchall()
        rules = [dict(row) for row in rows]
        conn.close()
        
        self._set_headers()
        self.wfile.write(json.dumps({
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": rules
        }).encode())

    def handle_create_rule(self):
        length = int(self.headers.get('Content-Length'))
        data = json.loads(self.rfile.read(length))
        
        rule_id = "R_" + str(uuid.uuid4())[:8].upper()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute("""INSERT INTO rules (rule_id, name, source_asset, target_asset, exchange_rate, step_size, min_amount, daily_limit, status, updated_by, updated_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (rule_id, data['name'], data['source_asset'], data['target_asset'], 
                       float(data['exchange_rate']), int(data['step_size']), int(data['min_amount']), 
                       int(data['daily_limit']), data['status'], "admin", now))
            conn.commit()
            self._set_headers(201)
            self.wfile.write(json.dumps({"message": "Created", "rule_id": rule_id}).encode())
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())
        finally:
            conn.close()

    def handle_update_rule(self, rule_id):
        length = int(self.headers.get('Content-Length'))
        data = json.loads(self.rfile.read(length))
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute("""UPDATE rules SET 
                         name=?, source_asset=?, target_asset=?, exchange_rate=?, 
                         step_size=?, min_amount=?, daily_limit=?, status=?, updated_at=?
                         WHERE rule_id=?""",
                      (data['name'], data['source_asset'], data['target_asset'], 
                       float(data['exchange_rate']), int(data['step_size']), int(data['min_amount']), 
                       int(data['daily_limit']), data['status'], now, rule_id))
            conn.commit()
            self._set_headers(200)
            self.wfile.write(json.dumps({"message": "Updated"}).encode())
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())
        finally:
            conn.close()

    def handle_delete_rule(self, rule_id):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute("DELETE FROM rules WHERE rule_id=?", (rule_id,))
            conn.commit()
            self._set_headers(200)
            self.wfile.write(json.dumps({"message": "Deleted"}).encode())
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())
        finally:
            conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Starting Admin Server on port {PORT}...")
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        httpd.serve_forever()
