import requests
import json
import csv
import time
import re
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.exceptions import InsecureRequestWarning
from datetime import datetime
from collections import defaultdict, Counter
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class BurpClusterBombEmulator:
    def __init__(self, request_file, output_csv="results.csv", keyword=None, max_workers=30, timeout=10):
        self.request_file = request_file
        self.output_csv = output_csv
        self.keyword = keyword
        self.max_workers = max_workers
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.results = []
        self.total_requests = 0
        self.completed = 0
        self.base_dir = os.path.dirname(os.path.abspath(request_file)) or os.getcwd()
        self.detected_keyword = None
        
    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {msg}")
    
    def parse_request(self):
        """Parsea la petición de Burp con marcadores §"""
        try:
            with open(self.request_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            self.log(f"Archivo no encontrado: {self.request_file}", "ERROR")
            sys.exit(1)
        
        # Normalizar HTTP/2 a HTTP/1.1
        content = content.replace('HTTP/2', 'HTTP/1.1')
        
        parts = content.split('\n\n', 1)
        if len(parts) < 2:
            self.log("No se encontró cuerpo en la petición", "ERROR")
            sys.exit(1)
        
        headers_part = parts[0]
        body_part = parts[1]
        
        lines = headers_part.split('\n')
        first_line = lines[0].strip()
        parts_line = first_line.split(' ')
        method = parts_line[0]
        url_path = parts_line[1] if len(parts_line) > 1 else '/'
        
        host_match = re.search(r'Host:\s*(.+?)(?:\n|$)', headers_part, re.IGNORECASE)
        if not host_match:
            self.log("No se encontró Host en las cabeceras", "ERROR")
            sys.exit(1)
        
        host = host_match.group(1).strip()
        base_url = f"https://{host}"
        
        headers = {}
        for line in lines[1:]:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
        
        # Eliminar cabeceras problemáticas
        headers.pop('Content-Length', None)
        headers.pop('Accept-Encoding', None)
        
        # Encontrar marcadores §
        pattern = r'§([^§]*)§'
        matches = list(re.finditer(pattern, body_part))
        
        if not matches:
            self.log("No se encontraron marcadores § en el cuerpo", "ERROR")
            sys.exit(1)
        
        positions = []
        for match in matches:
            positions.append({
                'start': match.start(),
                'end': match.end(),
                'placeholder': match.group(1)
            })
        
        self.log(f"Encontrados {len(positions)} marcadores en la petición")
        
        return {
            'method': method,
            'base_url': base_url,
            'url_path': url_path,
            'headers': headers,
            'body': body_part,
            'positions': positions,
            'original_body': body_part
        }
    
    def load_payloads(self, positions):
        """Carga las payloads para cada posición"""
        payloads = {}
        
        for i, pos in enumerate(positions):
            placeholder = pos['placeholder']
            
            if placeholder.endswith('.txt'):
                file_path = os.path.join(self.base_dir, placeholder)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        payloads[i] = [line.strip() for line in f if line.strip()]
                    self.log(f"Cargadas {len(payloads[i])} payloads desde {placeholder}")
                except FileNotFoundError:
                    self.log(f"Archivo no encontrado: {placeholder}", "WARNING")
                    payloads[i] = ['default']
            else:
                items = [p.strip() for p in placeholder.split(',') if p.strip()]
                if items:
                    payloads[i] = items
                    self.log(f"Cargadas {len(payloads[i])} payloads inline para posición {i}")
                else:
                    payloads[i] = ['default']
        
        return payloads
    
    def generate_combinations(self, payloads):
        """Genera todas las combinaciones de payloads (cluster bomb)"""
        import itertools
        
        payload_lists = [payloads[i] for i in sorted(payloads.keys())]
        combinations = list(itertools.product(*payload_lists))
        
        self.log(f"Total de combinaciones: {len(combinations)}")
        return combinations
    
    def build_request(self, parsed, combination):
        """Construye la petición con las payloads insertadas"""
        body = parsed['original_body']
        positions = parsed['positions']
        
        for i, pos in enumerate(reversed(positions)):
            start = pos['start']
            end = pos['end']
            body = body[:start] + combination[len(positions) - 1 - i] + body[end:]
        
        return body
    
    def send_request(self, parsed, combination, combination_id):
        """Envía una petición con la combinación específica"""
        body = self.build_request(parsed, combination)
        url = parsed['base_url'] + parsed['url_path']
        method = parsed['method']
        headers = parsed['headers'].copy()
        headers['Content-Length'] = str(len(body))
        
        try:
            start_time = time.time()
            content_type = headers.get('Content-Type', '')
            
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                if 'application/json' in content_type:
                    try:
                        json_body = json.loads(body)
                        response = self.session.post(url, json=json_body, headers=headers, timeout=self.timeout)
                    except:
                        response = self.session.post(url, data=body, headers=headers, timeout=self.timeout)
                else:
                    response = self.session.post(url, data=body, headers=headers, timeout=self.timeout)
            else:
                response = self.session.request(method.upper(), url, data=body, headers=headers, timeout=self.timeout)
            
            elapsed = time.time() - start_time
            
            return {
                'combination_id': combination_id,
                'combination': '|'.join(combination),
                'status_code': response.status_code,
                'response_length': len(response.text),
                'response_time': round(elapsed, 3),
                'response_text': response.text,
                'response_preview': response.text[:300].replace('\n', ' ').replace(',', ';')
            }
            
        except requests.exceptions.Timeout:
            return {
                'combination_id': combination_id,
                'combination': '|'.join(combination),
                'status_code': 408,
                'response_length': 0,
                'response_time': self.timeout,
                'response_text': 'TIMEOUT',
                'response_preview': 'TIMEOUT'
            }
        except Exception as e:
            return {
                'combination_id': combination_id,
                'combination': '|'.join(combination),
                'status_code': 0,
                'response_length': 0,
                'response_time': 0,
                'response_text': str(e)[:100],
                'response_preview': str(e)[:100]
            }
    
    def detect_keyword(self, results):
        """Detecta automáticamente la palabra clave comparando respuestas"""
        self.log("Detectando palabra clave automáticamente...")
        
        # Agrupar por status_code
        by_status = defaultdict(list)
        for r in results:
            by_status[r['status_code']].append(r)
        
        # Usar el status más común
        if 200 in by_status and len(by_status[200]) > 1:
            responses = by_status[200]
        else:
            most_common = Counter(r['status_code'] for r in results).most_common(1)[0][0]
            responses = by_status[most_common]
        
        # Buscar patrones comunes
        common_patterns = [
            'Account locked', 'locked',
            'Invalid', 'invalid',
            'Error', 'error',
            'Success', 'success',
            'Welcome', 'welcome'
        ]
        
        for pattern in common_patterns:
            for r in responses:
                if pattern in r['response_text']:
                    self.log(f"Palabra clave detectada: '{pattern}'", "SUCCESS")
                    return pattern
        
        # Si no se encuentra, buscar diferencias significativas
        if len(responses) > 1:
            base_text = responses[0]['response_text']
            for r in responses[1:]:
                if abs(len(r['response_text']) - len(base_text)) > 50:
                    # Buscar frases que indiquen éxito/fallo
                    for pattern in common_patterns:
                        if pattern in r['response_text'] and pattern not in base_text:
                            self.log(f"Palabra clave detectada por diferencia: '{pattern}'", "SUCCESS")
                            return pattern
        
        self.log("No se pudo detectar palabra clave, usando 'Account locked'", "WARNING")
        return "Account locked"
    
    def progress_callback(self, future):
        self.completed += 1
        if self.completed % 10 == 0 or self.completed == self.total_requests:
            percent = (self.completed / self.total_requests) * 100
            print(f"\r  Progreso: {self.completed}/{self.total_requests} ({percent:.1f}%)", end="", flush=True)
    
    def run_attack(self):
        self.log("=== INICIANDO CLUSTER BOMB EMULATOR ===")
        
        parsed = self.parse_request()
        self.log(f"URL: {parsed['base_url']}{parsed['url_path']}")
        
        payloads = self.load_payloads(parsed['positions'])
        combinations = self.generate_combinations(payloads)
        self.total_requests = len(combinations)
        
        if self.total_requests == 0:
            self.log("No hay combinaciones para probar", "ERROR")
            return
        
        self.log(f"Enviando {self.total_requests} peticiones con {self.max_workers} hilos...")
        self.log("Esto puede tomar unos minutos...")
        
        start_time = time.time()
        self.completed = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for i, combo in enumerate(combinations):
                future = executor.submit(self.send_request, parsed, combo, i)
                future.add_done_callback(self.progress_callback)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    self.results.append(result)
                except Exception as e:
                    self.log(f"Error en petición: {e}", "ERROR")
        
        elapsed = time.time() - start_time
        print()
        self.log(f"Completado en {elapsed:.2f} segundos")
        
        # Detectar palabra clave si no se proporcionó
        if not self.keyword:
            self.keyword = self.detect_keyword(self.results)
        
        self.save_results()
        self.analyze_results()
    
    def save_results(self):
        if not self.results:
            self.log("No hay resultados para guardar", "WARNING")
            return
        
        self.results.sort(key=lambda x: x['combination_id'])
        
        fieldnames = ['combination_id', 'combination', 'status_code', 'response_length', 
                     'response_time', f'contains_{self.keyword.replace(" ", "_")}', 'response_preview']
        
        with open(self.output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                row = {
                    'combination_id': result.get('combination_id', ''),
                    'combination': result.get('combination', ''),
                    'status_code': result.get('status_code', ''),
                    'response_length': result.get('response_length', ''),
                    'response_time': result.get('response_time', ''),
                    f'contains_{self.keyword.replace(" ", "_")}': self.keyword in result.get('response_text', ''),
                    'response_preview': result.get('response_preview', '')
                }
                writer.writerow(row)
        
        self.log(f"Resultados guardados en: {self.output_csv}")
    
    def analyze_results(self):
        self.log("=== ANÁLISIS RÁPIDO ===")
        self.log(f"Palabra clave: '{self.keyword}'")
        
        status_counts = defaultdict(int)
        for r in self.results:
            status_counts[r.get('status_code', 0)] += 1
        
        self.log("Distribución de status codes:")
        for status, count in sorted(status_counts.items()):
            if status == 0:
                self.log(f"  Error: {count} peticiones")
            else:
                self.log(f"  {status}: {count} peticiones")
        
        # Buscar la palabra clave
        matches = [r for r in self.results if self.keyword in r.get('response_text', '')]
        if matches:
            self.log(f"✅ Encontradas {len(matches)} peticiones con '{self.keyword}'", "SUCCESS")
            for r in matches[:20]:
                self.log(f"  ID {r['combination_id']}: {r['combination']} -> {self.keyword}")
        else:
            self.log(f"❌ No se encontraron peticiones con '{self.keyword}'")
        
        # Mostrar estadísticas de respuestas
        response_lengths = [r['response_length'] for r in self.results]
        if response_lengths:
            avg_len = sum(response_lengths) / len(response_lengths)
            min_len = min(response_lengths)
            max_len = max(response_lengths)
            self.log(f"Longitudes de respuesta - Promedio: {avg_len:.0f}, Min: {min_len}, Max: {max_len}")
        
        self.log(f"Total peticiones: {len(self.results)}")
        if self.results:
            valid_times = [r['response_time'] for r in self.results if r.get('response_time', 0) > 0]
            if valid_times:
                avg_time = sum(valid_times) / len(valid_times)
                self.log(f"Tiempo promedio: {avg_time:.2f}s")

def main():
    if len(sys.argv) < 2:
        print("="*60)
        print("CLUSTER BOMB EMULATOR - VERSIÓN UNIVERSAL")
        print("="*60)
        print("\nUso: python cluster-bomb.py <archivo_peticion.txt> [archivo_csv_salida] [palabra_clave]")
        print("\nEjemplos:")
        print("  python cluster-bomb.py request.txt")
        print("  python cluster-bomb.py request.txt resultados.csv")
        print("  python cluster-bomb.py request.txt resultados.csv 'Account locked'")
        print("  python cluster-bomb.py request.txt resultados.csv 'Invalid username'")
        print("\nCaracterísticas:")
        print("  ✅ Detecta automáticamente la palabra clave si no se proporciona")
        print("  ✅ Soporta HTTP/1.1 y HTTP/2")
        print("  ✅ Soporta cabeceras completas de Burp")
        print("  ✅ Guarda resultados en CSV")
        print("="*60)
        sys.exit(1)
    
    request_file = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else "resultados.csv"
    keyword = sys.argv[3] if len(sys.argv) > 3 else None
    
    emulator = BurpClusterBombEmulator(
        request_file=request_file,
        output_csv=output_csv,
        keyword=keyword,
        max_workers=30,
        timeout=10
    )
    
    emulator.run_attack()

if __name__ == "__main__":
    main()
