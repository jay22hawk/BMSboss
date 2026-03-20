"""
BMS Boss — Extraction Service (stdlib HTTP server)
API endpoints for bill extraction and Excel generation.
Uses Python's built-in http.server since FastAPI can't be installed in this env.
"""

import os
import sys
import uuid
import json
import shutil
import dataclasses
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import date
from enum import Enum

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (
    BMSCalculatorInput, ExtractionResponse, GenerationResponse,
    ExtractedBillData, AffectedArea
)
from extractor import extract_bill
from excel_generator import generate_calculator, merge_bill_data_to_calculator, get_template_info, update_template

# Temp directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))

CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]


class EnhancedJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles dataclasses, Enums, dates."""
    def default(self, o):
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, date):
            return o.isoformat()
        return super().default(o)


def parse_multipart(handler):
    """Parse multipart/form-data to extract uploaded file."""
    content_type = handler.headers.get('Content-Type', '')
    if 'multipart/form-data' not in content_type:
        return None, None

    # Extract boundary
    boundary = None
    for part in content_type.split(';'):
        part = part.strip()
        if part.startswith('boundary='):
            boundary = part.split('=', 1)[1].strip('"')
            break

    if not boundary:
        return None, None

    content_length = int(handler.headers.get('Content-Length', 0))
    body = handler.rfile.read(content_length)

    boundary_bytes = boundary.encode()
    parts = body.split(b'--' + boundary_bytes)

    for part in parts:
        if b'Content-Disposition' not in part:
            continue

        # Split headers from body
        header_end = part.find(b'\r\n\r\n')
        if header_end == -1:
            continue

        headers_raw = part[:header_end].decode('utf-8', errors='replace')
        file_data = part[header_end + 4:]

        # Trim trailing \r\n
        if file_data.endswith(b'\r\n'):
            file_data = file_data[:-2]

        # Get filename from Content-Disposition
        filename = None
        for line in headers_raw.split('\r\n'):
            if 'filename=' in line:
                for segment in line.split(';'):
                    segment = segment.strip()
                    if segment.startswith('filename='):
                        filename = segment.split('=', 1)[1].strip('"')
                        break

        if filename:
            return filename, file_data

    return None, None


class BMSBossHandler(BaseHTTPRequestHandler):
    """HTTP request handler for BMS Boss extraction service."""

    def _set_cors_headers(self):
        origin = self.headers.get('Origin', '')
        if origin in CORS_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
        else:
            self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _send_json(self, data, status=200):
        body = json.dumps(data, cls=EnhancedJSONEncoder).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status, message):
        self._send_json({"error": message}, status)

    def _send_file(self, file_path, filename, media_type):
        with open(file_path, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', media_type)
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self._set_cors_headers()
        self.send_header('Content-Length', len(data))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        if path == '/health':
            self._send_json({
                "status": "healthy",
                "service": "bms-boss-extraction",
                "endpoints": [
                    "/health", "/extract", "/generate", "/extract-and-merge",
                    "/download/<file_id>", "/admin/template", "/admin/parsers",
                ]
            })

        elif path == '/admin/template':
            # Return info about the currently active BMS Calculator template
            self._send_json(get_template_info())

        elif path == '/admin/parsers':
            # Return list of registered bill parsers and their status
            from extractor import PARSERS
            self._send_json({
                "parsers": [
                    {"name": p.sponsor_name, "type": p.__class__.__name__}
                    for p in PARSERS
                ]
            })

        elif path.startswith('/download/'):
            file_id = path.split('/download/')[-1]
            file_path = OUTPUT_DIR / f"BMS_Calculator_{file_id}.xlsx"
            if not file_path.exists():
                self._send_error(404, "File not found")
                return
            self._send_file(
                str(file_path),
                f"Prescriptive_BMS_Calculator_{file_id}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        elif path == '' or path == '/index.html':
            self._serve_static('index.html')

        elif path.startswith('/static/'):
            filename = path.split('/static/')[-1]
            self._serve_static(filename)

        else:
            self._send_error(404, f"Not found: {path}")

    def _serve_static(self, filename):
        """Serve static files from the static/ directory."""
        static_dir = Path(__file__).parent / "static"
        file_path = static_dir / filename
        if not file_path.exists() or not file_path.is_file():
            self._send_error(404, f"Static file not found: {filename}")
            return

        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
        }
        ext = file_path.suffix.lower()
        content_type = content_types.get(ext, 'application/octet-stream')

        with open(file_path, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(data))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        if path == '/extract':
            self._handle_extract()
        elif path == '/generate':
            self._handle_generate()
        elif path == '/extract-and-merge':
            self._handle_extract_and_merge()
        elif path == '/admin/template':
            self._handle_template_upload()
        else:
            self._send_error(404, f"Not found: {path}")

    def _handle_extract(self):
        """Upload a utility bill PDF and extract structured data."""
        filename, file_data = parse_multipart(self)
        if not filename or not file_data:
            self._send_error(400, "No file uploaded. Send multipart/form-data with a 'file' field.")
            return

        if not filename.lower().endswith('.pdf'):
            self._send_error(400, "Only PDF files are accepted")
            return

        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}.pdf"

        try:
            with open(file_path, 'wb') as f:
                f.write(file_data)

            result = extract_bill(str(file_path))
            self._send_json(dataclasses.asdict(result))

        except Exception as e:
            self._send_error(500, f"Extraction failed: {str(e)}")
        finally:
            if file_path.exists():
                file_path.unlink()

    def _handle_generate(self):
        """Generate a BMS Calculator Excel file from JSON input."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON body")
            return

        file_id = str(uuid.uuid4())
        output_path = OUTPUT_DIR / f"BMS_Calculator_{file_id}.xlsx"

        try:
            calculator_input = _dict_to_calculator_input(data)
            result = generate_calculator(
                calculator_input=calculator_input,
                output_path=str(output_path),
            )
            response = dataclasses.asdict(result)
            response['file_id'] = file_id
            response['download_url'] = f"/download/{file_id}"
            self._send_json(response)

        except Exception as e:
            self._send_error(500, f"Generation failed: {str(e)}")

    def _handle_extract_and_merge(self):
        """Upload a bill PDF, extract data, and return pre-populated calculator input."""
        filename, file_data = parse_multipart(self)
        if not filename or not file_data:
            self._send_error(400, "No file uploaded. Send multipart/form-data with a 'file' field.")
            return

        if not filename.lower().endswith('.pdf'):
            self._send_error(400, "Only PDF files are accepted")
            return

        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}.pdf"

        try:
            with open(file_path, 'wb') as f:
                f.write(file_data)

            extraction = extract_bill(str(file_path))

            if not extraction.success or not extraction.data:
                self._send_json({
                    "success": False,
                    "extraction": dataclasses.asdict(extraction),
                    "calculator_input": None,
                })
                return

            calculator_input = BMSCalculatorInput()
            calculator_input = merge_bill_data_to_calculator(
                extraction.data, calculator_input
            )

            self._send_json({
                "success": True,
                "extraction": dataclasses.asdict(extraction),
                "calculator_input": dataclasses.asdict(calculator_input),
            })

        except Exception as e:
            self._send_error(500, f"Extract-and-merge failed: {str(e)}")
        finally:
            if file_path.exists():
                file_path.unlink()

    def _handle_template_upload(self):
        """Admin: Upload a new BMS Calculator template to replace the current one."""
        filename, file_data = parse_multipart(self)
        if not filename or not file_data:
            self._send_error(400, "No file uploaded. Send multipart/form-data with an .xlsx file.")
            return

        if not filename.lower().endswith('.xlsx'):
            self._send_error(400, "Only .xlsx files are accepted as templates")
            return

        # Basic validation: ensure it's a real Excel file (check magic bytes)
        if not file_data[:4] == b'PK\x03\x04':
            self._send_error(400, "File does not appear to be a valid .xlsx file")
            return

        try:
            result = update_template(file_data, filename)
            self._send_json(result)
        except Exception as e:
            self._send_error(500, f"Template update failed: {str(e)}")

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[BMS Boss] {self.client_address[0]} - {format % args}")


def _dict_to_calculator_input(data: dict) -> BMSCalculatorInput:
    """Convert a JSON dict to BMSCalculatorInput dataclass, handling enum conversion."""
    from models import (
        BuildingActivity, HeatingFuel, ProjectType,
        VentilationType, HeatingSystemType, CoolingSystemType, TerminalUnitType
    )

    # Enum field mappings for BMSCalculatorInput
    calc_enum_fields = {
        'building_activity': BuildingActivity,
        'heating_fuel': HeatingFuel,
        'project_type': ProjectType,
    }

    # Enum field mappings for AffectedArea
    area_enum_fields = {
        'ventilation_type': VentilationType,
        'primary_heating': HeatingSystemType,
        'primary_cooling': CoolingSystemType,
        'terminal_units': TerminalUnitType,
        'secondary_heating_to_hp': HeatingSystemType,
    }

    def _convert_enum(value, enum_cls):
        if value is None or isinstance(value, enum_cls):
            return value
        # Try matching by value
        for member in enum_cls:
            if member.value == value:
                return member
        return value  # Return as-is if no match

    areas_data = data.pop('affected_areas', [])
    areas = []
    for area_dict in areas_data:
        for field_name, enum_cls in area_enum_fields.items():
            if field_name in area_dict:
                area_dict[field_name] = _convert_enum(area_dict[field_name], enum_cls)
        area = AffectedArea(**{k: v for k, v in area_dict.items() if hasattr(AffectedArea, k)})
        areas.append(area)

    # Convert enum fields in main data
    for field_name, enum_cls in calc_enum_fields.items():
        if field_name in data:
            data[field_name] = _convert_enum(data[field_name], enum_cls)

    calc = BMSCalculatorInput(
        **{k: v for k, v in data.items() if hasattr(BMSCalculatorInput, k) and k != 'affected_areas'}
    )
    calc.affected_areas = areas
    return calc


def main():
    server = HTTPServer((HOST, PORT), BMSBossHandler)
    tmpl_info = get_template_info()
    tmpl_status = f"Loaded: {tmpl_info['filename']}" if tmpl_info['has_template'] else "NOT FOUND"
    print(f"""
╔══════════════════════════════════════════════════════════╗
║          BMS Boss — Extraction Service v0.2.0           ║
╠══════════════════════════════════════════════════════════╣
║  Server running at http://{HOST}:{PORT}                  ║
║  Template: {tmpl_status:<45}║
║                                                          ║
║  Endpoints:                                              ║
║    GET  /health            — Service health check        ║
║    POST /extract           — Extract data from bill PDF  ║
║    POST /generate          — Generate BMS Calculator xlsx║
║    POST /extract-and-merge — Extract + pre-fill form     ║
║    GET  /download/<id>     — Download generated Excel    ║
║    GET  /admin/template    — View template info          ║
║    POST /admin/template    — Upload new template         ║
║    GET  /admin/parsers     — List supported utilities    ║
╚══════════════════════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
