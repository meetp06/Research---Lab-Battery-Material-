import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from opti_battery.core.analyzer import compute_interface_stability
from opti_battery.core.screener import screen_battery_materials
from opti_battery.core.structures import get_structure_cif
from opti_battery.core.performance import calculate_electrode_performance
from opti_battery.core.diffusion import analyze_lithium_diffusion
from opti_battery.core.voltage_window import calculate_voltage_window
from opti_battery.core.custom_screener import analyze_custom_cif
from opti_battery.core.piezo import get_top_piezo_materials
from opti_battery.core.synthesis import generate_cro_rfq
from opti_battery.monitor import store as discovery_store
from opti_battery.monitor.chatbot import answer as chatbot_answer

SCAN_PROCESS = None

TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "index.html"
RESEARCH_MD_PATH = Path(__file__).resolve().parents[3] / "RESEARCH.md"

class ServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            try:
                with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Error loading template: {str(e)}".encode("utf-8"))
        elif self.path == "/api/candidates":
            try:
                candidates = screen_battery_materials()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(candidates).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        elif self.path.startswith("/api/structure/"):
            try:
                material_id = self.path.split("/")[-1]
                cif_str = get_structure_cif(material_id)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"cif": cif_str}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        elif self.path == "/api/research":
            try:
                text = RESEARCH_MD_PATH.read_text(encoding="utf-8") \
                    if RESEARCH_MD_PATH.exists() else "# Our Research\n\n(RESEARCH.md not found)"
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"markdown": text}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        elif self.path == "/api/discovery":
            try:
                state = discovery_store.load_state()
                history = discovery_store.load_history()
                payload = {
                    "last_scan": state.get("last_scan"),
                    "champions": state.get("champions", {}),
                    "history": history[:50],
                }
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        elif self.path == "/api/piezo":
            try:
                candidates = get_top_piezo_materials(limit=20)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"candidates": candidates}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length else b""
        
        try:
            params = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            params = {}

        if self.path == "/api/interface-stability":
            try:
                electrolyte = params.get("electrolyte")
                anode = params.get("anode")
                cathode = params.get("cathode")
                if not electrolyte or not anode or not cathode:
                    raise ValueError("Missing parameters.")
                result = compute_interface_stability(electrolyte, anode, cathode)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                
        elif self.path == "/api/performance":
            try:
                formula = params.get("formula")
                if not formula:
                    raise ValueError("Missing formula parameter.")
                result = calculate_electrode_performance(formula)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                
        elif self.path == "/api/diffusion":
            try:
                material_id = params.get("material_id")
                if not material_id:
                    raise ValueError("Missing material_id parameter.")
                result = analyze_lithium_diffusion(material_id)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                
        elif self.path == "/api/voltage-window":
            try:
                formula = params.get("formula")
                if not formula:
                    raise ValueError("Missing formula parameter.")
                result = calculate_voltage_window(formula)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                
        elif self.path == "/api/analyze-custom-cif":
            try:
                cif = params.get("cif")
                if not cif:
                    raise ValueError("Missing 'cif' parameter.")
                result = analyze_custom_cif(cif)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        elif self.path == "/api/chat":
            try:
                question = params.get("question")
                if not question:
                    raise ValueError("Missing 'question' parameter.")
                result = chatbot_answer(question)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        elif self.path == "/api/generate-rfq":
            try:
                cif_str = params.get("cif")
                if not cif_str:
                    raise ValueError("Missing 'cif' parameter.")
                result = generate_cro_rfq(cif_str)
                self.send_response(200 if result.get("success") else 400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        elif self.path == "/api/run-scan":
            global SCAN_PROCESS
            import subprocess
            try:
                if SCAN_PROCESS is not None and SCAN_PROCESS.poll() is None:
                    raise ValueError("A scan is already running! Please wait for it to finish.")
                monitor_script = Path(__file__).resolve().parents[3] / "run_monitor.py"
                # Launch in background
                SCAN_PROCESS = subprocess.Popen([sys.executable, str(monitor_script), "--papers"])
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "Scan started in background! This may take up to 10 minutes. Click 'Refresh Discovery Feed' later to see results."}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")

def run_server(port=8085):
    server_address = ("", port)
    httpd = HTTPServer(server_address, ServerHandler)
    print(f"Starting server on http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        sys.exit(0)
