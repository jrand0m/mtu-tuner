# mtu-tuner
So i needed to tune mtu so i have created a script to make this optimisation.

📡 Automatically test and rank the best MTU for your network by measuring ICMP latency and HTTP upload speed across payload sizes.

---

## 🔧 Features

- Tests multiple MTU values
- Measures ping latency (ICMP)
- Uploads multiple payload sizes (1KB to 5MB)
- Performs repeated measurements
- Calculates score + % deviation from medians
- Real-time CLI output

---

## 🐍 Requirements

- Python 3.8+
- [`ping3`](https://pypi.org/project/ping3/)
- [`requests`](https://pypi.org/project/requests/)

Install:

```bash
pip install -r requirements.txt
```
## 🚀Usage

```bash
python mtu_tester.py --ping 1.1.1.1 --url http://localhost:8080/post
```

## Test server

So you will need a test server that will accept post payload. Use this docker compose file:

 ```docker-compose
version: "3.9"

services:
  mtu_test_server:
    image: python:3.11-slim
    container_name: mtu_test_server
    working_dir: /app
    ports:
      - "8080:5000"
    command: >
      sh -c "pip install flask && python -c '
from flask import Flask, request
import time
app = Flask(__name__)
@app.route(\"/post\", methods=[\"POST\"])
def handle():
    t0 = time.time()
    size = len(request.data)
    dt = time.time() - t0
    return {\"received\": size, \"time_sec\": round(dt, 4)}, 200
app.run(host=\"0.0.0.0\", port=5000)'"
```




