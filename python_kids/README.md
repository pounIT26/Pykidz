# 🐍 Python Adventure — Kids Coding Platform

A LeetCode-style Python learning platform for grades 4–5.
Runs entirely on YOUR PC as the server.

---

## 🚀 Quick Start (3 steps)

### Step 1 — Install Flask
Open a terminal and run:
```
pip install flask
```

### Step 2 — Start the server
Navigate to this folder and run:
```
python server.py
```

You should see:
```
🐍 Python Kids Server starting...
📡 Open your browser at: http://localhost:5000
```

### Step 3 — Open the site
Open your browser and go to:
```
http://localhost:5000
```

That's it! 🎉

---

## 📁 Project Structure

```
python_kids/
├── server.py          ← Flask backend (run this!)
├── requirements.txt   ← Python dependencies
├── README.md          ← This file
└── static/
    └── index.html     ← Full frontend (editor + tests)
```

---

## ✨ Features

- **8 Lessons** covering core Python concepts
- **Live Python editor** with syntax highlighting (CodeMirror)
- **Run button** — execute code instantly
- **Submit button** — runs hidden test cases (LeetCode-style)
- **Test validator** — output match + hidden unit tests
- **Progress tracking** — saved in browser (localStorage)
- **Confetti** 🎉 when a kid passes all tests
- **Auto-advance** to next exercise on success
- **Sandboxed** — dangerous imports are blocked for safety

---

## 🔒 Safety

The server blocks these in student code:
- `import os`, `import sys`, `import subprocess`
- `import socket`, `import urllib`, `import requests`
- `open()`, `exec()`, `eval()`, `__import__`

Code runs in a separate process with a 5-second timeout.

---

## 🌐 Share with students on your network

To let students on the same WiFi connect, run:
```
python server.py --host
```

Or edit server.py last line:
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

Then students visit: `http://YOUR_PC_IP:5000`
(Find your IP with `ipconfig` on Windows or `ifconfig` on Mac/Linux)

---

## ➕ Adding More Exercises

Open `server.py` and add to the `EXERCISES` dictionary:

```python
"l1_e4": {
    "title": "My Exercise",
    "lesson": 1,
    "description": "What the student should do.",
    "starter": '# Starter code here\n',
    "inject_input": ["test_input"],   # optional: auto-fed to input()
    "output_match": "expected output",  # optional: exact match check
    "tests": [
        {
            "description": "Must print something",
            "check": "min_line_count",
            "expected": 1
        }
    ]
}
```

### Available test check types:
| Check | Description |
|---|---|
| `line_count` | Output has exactly N lines |
| `min_line_count` | Output has at least N lines |
| `output_contains` | Output contains a string |
| `output_contains_any` | Output contains any of a list |
| `code_contains` | Source code contains a string |
| `contains_input` | Output mentions the injected input |
| `all_lines_nonempty` | Every output line has text |
