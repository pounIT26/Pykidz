"""
Python Kids - Flask + SocketIO Server
Real interactive terminal — input() works live!

Install:  pip install flask flask-socketio
Run:      python server.py
Open:     http://localhost:5000
"""
from gevent import monkey
monkey.patch_all()

from flask import Flask, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room
import subprocess, sys, os, tempfile, threading, re, json


app    = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'pythonkids2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent', engineio_logger=False)


# active sessions: sid → {proc, tmp}
sessions = {}

# ──────────────────────────────────────────────────────────────────────────
# EXERCISES
# ──────────────────────────────────────────────────────────────────────────
EXERCISES = {
    "l1_e1": {
        "title": "Hello, Me!",
        "lesson": 1,
        "description": "Print your name, your grade, and your favorite animal — each on its own line.",
        "starter": '# Print three things, one per line\nprint("Your Name")\nprint("Grade 4")\nprint("Dog")\n',
        "tests": [
            {"description": "Must print at least 3 lines",   "check": "min_line_count", "expected": 3},
            {"description": "Each line must have some text",  "check": "all_lines_nonempty", "expected": True},
        ]
    },
    "l1_e2": {
        "title": "Greeting Machine",
        "lesson": 1,
        "description": "Ask for the user's name with input(), then print: Hello, [name]!",
        "starter": 'name = input("What is your name? ")\n# Now print the greeting\n',
        "inject_input": ["Alex"],
        "tests": [
            {"description": "Must use input()",                     "check": "code_contains",   "expected": "input"},
            {"description": "Output must contain 'Hello'",          "check": "output_contains", "expected": "Hello"},
            {"description": "Output must contain the name entered", "check": "contains_input",  "input_index": 0},
        ]
    },
    "l1_e3": {
        "title": "My Info Card",
        "lesson": 1,
        "description": "Ask for name AND favorite color, then print a sentence combining both.",
        "starter": 'name  = input("Your name: ")\ncolor = input("Favorite color: ")\n# Print a sentence using both\n',
        "inject_input": ["Jordan", "blue"],
        "tests": [
            {"description": "Output must mention the name",  "check": "contains_input", "input_index": 0},
            {"description": "Output must mention the color", "check": "contains_input", "input_index": 1},
        ]
    },

    "l2_e1": {
        "title": "My Profile",
        "lesson": 2,
        "description": "Create 4 variables: name, age, grade, favorite_subject. Print them all.",
        "starter": 'grade            = 0\nfavorite_subject = ""\n# Print all four\n',
        "tests": [
            {"description": "Must print at least 4 lines",      "check": "min_line_count", "expected": 4},
            {"description": "Code must define variable 'name'", "check": "code_contains",  "expected": "name"},
            {"description": "Code must define variable 'age'",  "check": "code_contains",  "expected": "age"},
        ]
    },
    "l2_e2": {
        "title": "Score Counter",
        "lesson": 2,
        "description": "Start score=0, add 10, add 25, subtract 5. Print after each step. Final = 30.",
        "starter": 'score = 0\n# Add 10, then add 25, then subtract 5\n# Print after every step\n',
        "tests": [
            {"description": "Final score must be 30",       "check": "output_contains", "expected": "30"},
            {"description": "Must print at least 4 times", "check": "min_line_count",   "expected": 4},
        ]
    },
    "l3_e1": {
        "title": "Simple Calculator",
        "lesson": 3,
        "description": "Ask for two numbers. Print their sum, difference, product, and quotient.",
        "starter": 'a = int(input("First number: "))\nb = int(input("Second number: "))\n# Print sum, difference, product, quotient\n',
        "inject_input": ["10", "4"],
        "tests": [
            {"description": "Must print the sum (14)",       "check": "output_contains", "expected": "14"},
            {"description": "Must print the difference (6)", "check": "output_contains", "expected": "6"},
            {"description": "Must print the product (40)",   "check": "output_contains", "expected": "40"},
        ]
    },
    "l3_e2": {
        "title": "Pizza Party Planner",
        "lesson": 3,
        "description": "Ask how many kids are coming. Each pizza has 8 slices, each kid eats 3. How many pizzas?",
        "starter": 'kids = int(input("How many kids? "))\n# Calculate pizzas needed\n# Hint: use // and %\n',
        "inject_input": ["8"],
        "tests": [
            {"description": "Must use integer division //", "check": "code_contains",  "expected": "//"},
            {"description": "Must print a number",          "check": "min_line_count", "expected": 1},
        ]
    },
    "l4_e1": {
        "title": "Age Checker",
        "lesson": 4,
        "description": "Ask for age. Print 'You can make a social media account!' if 13+, else too young.",
        "starter": 'age = int(input("How old are you? "))\n# Check the age\n',
        "inject_input": ["15"],
        "tests": [
            {"description": "Age 15 → should allow social media", "check": "output_contains_any", "expected": ["can", "allowed", "account"]},
            {"description": "Code must use 'if'",                 "check": "code_contains",        "expected": "if"},
        ]
    },
    "l4_e2": {
        "title": "Secret Door Game",
        "lesson": 4,
        "description": "Ask for a password. If correct → 'Door opens!'. Otherwise → 'Wrong password!'",
        "starter": 'password = input("Enter the password: ")\n# Check the password\n',
        "inject_input": ["dragon"],
        "tests": [
            {"description": "Code must use == to compare", "check": "code_contains",  "expected": "=="},
            {"description": "Code must have if AND else",  "check": "code_contains",  "expected": "else"},
            {"description": "Must print something",        "check": "min_line_count", "expected": 1},
        ]
    },
    "l5_e1": {
        "title": "Countdown Rocket",
        "lesson": 5,
        "description": "Count DOWN from 10 to 1 with a for loop, then print 'BLAST OFF!'",
        "starter": '#for i in range(10, 0, -1):\n    ',
        "tests": [
            {"description": "Must print 10",        "check": "output_contains", "expected": "10"},
            {"description": "Must print 1",         "check": "output_contains", "expected": "1"},
            {"description": "Must print BLAST OFF", "check": "output_contains", "expected": "BLAST OFF"},
            {"description": "Must use a for loop",  "check": "code_contains",   "expected": "for"},
        ]
    },
    "l5_e2": {
        "title": "Multiplication Table",
        "lesson": 5,
        "description": "Ask for a number. Print its multiplication table from 1 to 10.",
        "starter": 'num = int(input("Enter a number: "))\nfor i in range(1, 11):\n    pass  # replace with print statement\n',
        "inject_input": ["3"],
        "tests": [
            {"description": "Must show result 3",  "check": "output_contains", "expected": "3"},
            {"description": "Must show result 30", "check": "output_contains", "expected": "30"},
            {"description": "Must print 10 lines", "check": "min_line_count",  "expected": 10},
        ]
    },
    "l6_e1": {
        "title": "Favorite Things",
        "lesson": 6,
        "description": "Create a list of 5 favorites. Print the whole list, first item, and last item.",
        "starter": 'favorites = ["item1", "item2", "item3", "item4", "item5"]\n# Print whole list\n# Print first item [0]\n# Print last item [-1]\n',
        "tests": [
            {"description": "Code must have a list variable", "check": "code_contains",  "expected": "favorites"},
            {"description": "Must use index [0]",             "check": "code_contains",  "expected": "[0]"},
            {"description": "Must print at least 3 lines",   "check": "min_line_count", "expected": 3},
        ]
    },
    "l7_e1": {
        "title": "Greeting Machine v2",
        "lesson": 7,
        "description": "Write greet(name, grade) that prints 'Hi [name], welcome to grade [grade]!' Call it 3 times.",
        "starter": 'def greet(name, grade):\n    pass  # write the print statement\n\ngreet("Alex",   4)\ngreet("Jordan", 5)\ngreet("Sam",    4)\n',
        "tests": [
            {"description": "Must define function 'def greet'",   "check": "code_contains",   "expected": "def greet"},
            {"description": "Must produce at least 3 lines out",  "check": "min_line_count",  "expected": 3},
            {"description": "Output must contain 'Alex'",         "check": "output_contains", "expected": "Alex"},
        ]
    },
    "l7_e2": {
        "title": "Math Helpers",
        "lesson": 7,
        "description": "Write square(n), cube(n), and average(a,b,c) — each must return a value.",
        "starter": 'def square(n):\n    return 0  # fix me\n\ndef cube(n):\n    return 0  # fix me\n\ndef average(a, b, c):\n    return 0  # fix me\n\nprint(square(4))           # should print 16\nprint(cube(3))             # should print 27\nprint(average(10, 20, 30)) # should print 20.0\n',
        "tests": [
            {"description": "square(4) must return 16",         "check": "output_contains", "expected": "16"},
            {"description": "cube(3) must return 27",           "check": "output_contains", "expected": "27"},
            {"description": "average(10,20,30) must return 20", "check": "output_contains", "expected": "20"},
        ]
    },

    # ── LESSON 4 EXTRA: More if/else logic ────────────────────────────────
    "l4_e3": {
        "title": "Grade Classifier",
        "lesson": 4,
        "description": "Ask for a score (0–100). Print the grade: A (90+), B (80+), C (70+), D (60+), F (below 60). Use elif!",
        "starter": 'score = int(input("Enter your score: "))\n# Use if / elif / else to print the grade\n',
        "inject_input": ["85"],
        "tests": [
            {"description": "Score 85 must print grade B",  "check": "output_contains", "expected": "B"},
            {"description": "Code must use elif",           "check": "code_contains",   "expected": "elif"},
            {"description": "Code must use if",             "check": "code_contains",   "expected": "if"},
        ]
    },
    "l4_e4": {
        "title": "Even, Odd, and Sign",
        "lesson": 4,
        "description": "Ask for a number. Print whether it is positive/negative/zero AND whether it is even or odd.",
        "starter": 'num = int(input("Enter a number: "))\n# Check positive / negative / zero\n# Check even / odd\n',
        "inject_input": ["6"],
        "tests": [
            {"description": "6 is positive — output must say so", "check": "output_contains_any", "expected": ["positive", "Positive"]},
            {"description": "6 is even — output must say so",     "check": "output_contains_any", "expected": ["even", "Even"]},
            {"description": "Code must use %",                    "check": "code_contains",        "expected": "%"},
        ]
    },
    "l4_e5": {
        "title": "Ticket Price",
        "lesson": 4,
        "description": "Ask for age. Tickets cost: under 5 → free, 5–12 → $5, 13–17 → $8, 18+ → $12. Print the price.",
        "starter": 'age = int(input("Enter age: "))\n# Figure out the ticket price using if / elif / else\n',
        "inject_input": ["10"],
        "tests": [
            {"description": "Age 10 → ticket costs $5",  "check": "output_contains", "expected": "5"},
            {"description": "Code must use elif",         "check": "code_contains",   "expected": "elif"},
            {"description": "Must print something",       "check": "min_line_count",  "expected": 1},
        ]
    },

    # ── LESSON 8: Dictionaries ─────────────────────────────────────────────
    "l8_e1": {
        "title": "Report Card",
        "lesson": 8,
        "description": "Create a dictionary with 3 subjects and your scores. Loop through it and print each subject with its score.",
        "starter": 'report = {\n    "Math":    95,\n    "English": 80,\n    "Science": 88,\n}\n# Loop through and print each subject and score\n',
        "tests": [
            {"description": "Code must use a dictionary {}",      "check": "code_contains",  "expected": "{"},
            {"description": "Code must loop with for",            "check": "code_contains",  "expected": "for"},
            {"description": "Must print at least 3 lines",        "check": "min_line_count", "expected": 3},
            {"description": "Output must mention Math",           "check": "output_contains", "expected": "Math"},
        ]
    },
    "l8_e2": {
        "title": "Word Frequency",
        "lesson": 8,
        "description": "Count how many times each word appears in this sentence: 'the cat sat on the mat the cat'. Print each word and its count.",
        "starter": 'sentence = "the cat sat on the mat the cat"\nwords = sentence.split()\ncounts = {}\n# Loop through words and count each one\n# Hint: counts[word] = counts.get(word, 0) + 1\n',
        "tests": [
            {"description": "Code must use a dictionary",        "check": "code_contains",   "expected": "counts"},
            {"description": "'the' appears 3 times",             "check": "output_contains", "expected": "3"},
            {"description": "'cat' appears 2 times",             "check": "output_contains", "expected": "2"},
        ]
    },

    # ── LESSON 9: String Methods ───────────────────────────────────────────
    "l9_e1": {
        "title": "Name Formatter",
        "lesson": 9,
        "description": "Ask for a full name. Print it in UPPERCASE, lowercase, and Title Case on separate lines.",
        "starter": 'name = input("Enter your full name: ")\n# Print uppercase, lowercase, title case\n',
        "inject_input": ["john doe"],
        "tests": [
            {"description": "Output must contain JOHN DOE (upper)",  "check": "output_contains", "expected": "JOHN DOE"},
            {"description": "Output must contain john doe (lower)",  "check": "output_contains", "expected": "john doe"},
            {"description": "Output must contain John Doe (title)",  "check": "output_contains", "expected": "John Doe"},
        ]
    },
    "l9_e2": {
        "title": "Palindrome Checker",
        "lesson": 9,
        "description": "Ask for a word. Print 'Yes, palindrome!' if it reads the same forwards and backwards, else 'Not a palindrome.'",
        "starter": 'word = input("Enter a word: ").lower()\n# Hint: reversed string is word[::-1]\n',
        "inject_input": ["racecar"],
        "tests": [
            {"description": "'racecar' is a palindrome",   "check": "output_contains_any", "expected": ["palindrome", "Palindrome", "yes", "Yes"]},
            {"description": "Code must use [::-1] or reversed", "check": "code_contains", "expected": "[::-1]"},
        ]
    },

    # ── LESSON 10: While Loops ─────────────────────────────────────────────
    "l10_e1": {
        "title": "Number Guessing Game",
        "lesson": 10,
        "description": "Secret number is 7. Keep asking the user to guess. Print 'Too low!', 'Too high!', or 'Correct!' Stop when they get it.",
        "starter": 'secret = 7\nguess = 0\nwhile guess != secret:\n    guess = int(input("Guess: "))\n    # Give a hint or say correct\n',
        "inject_input": ["3", "9", "7"],
        "tests": [
            {"description": "Code must use while",                         "check": "code_contains",        "expected": "while"},
            {"description": "Must print a too-low/high hint",              "check": "output_contains_any",  "expected": ["low", "high", "Low", "High"]},
            {"description": "Must print correct when guess is right",      "check": "output_contains_any",  "expected": ["Correct", "correct", "got it", "Yes"]},
        ]
    },
    "l10_e2": {
        "title": "Sum Until Zero",
        "lesson": 10,
        "description": "Keep asking for numbers and add them to a total. Stop when the user enters 0. Print the final total.",
        "starter": 'total = 0\n# Use a while loop — stop when input is 0\n',
        "inject_input": ["5", "10", "3", "0"],
        "tests": [
            {"description": "Code must use while",          "check": "code_contains",   "expected": "while"},
            {"description": "Final total must be 18",       "check": "output_contains", "expected": "18"},
            {"description": "Must print the total",         "check": "min_line_count",  "expected": 1},
        ]
    },

    # ── LESSON 11: Recursion (Advanced) ───────────────────────────────────
    "l11_e1": {
        "title": "Factorial",
        "lesson": 11,
        "description": "Write a RECURSIVE function factorial(n) that returns n! (e.g. factorial(5) = 120). Call it and print the result.",
        "starter": 'def factorial(n):\n    if n == 0:\n        return 1\n    # What goes here? Think: n * factorial of what?\n\nprint(factorial(5))   # should print 120\nprint(factorial(0))   # should print 1\nprint(factorial(3))   # should print 6\n',
        "tests": [
            {"description": "factorial(5) must return 120", "check": "output_contains", "expected": "120"},
            {"description": "factorial(0) must return 1",   "check": "output_contains", "expected": "1"},
            {"description": "factorial(3) must return 6",   "check": "output_contains", "expected": "6"},
            {"description": "Must use recursion (def + return)", "check": "code_contains", "expected": "factorial("},
        ]
    },
    "l11_e2": {
        "title": "Fibonacci",
        "lesson": 11,
        "description": "Write fib(n) that returns the nth Fibonacci number. fib(1)=1, fib(2)=1, fib(10)=55. Print fib(1) through fib(10).",
        "starter": 'def fib(n):\n    if n <= 1:\n        return 1\n    # What goes here?\n\nfor i in range(1, 11):\n    print(fib(i))\n',
        "tests": [
            {"description": "fib(10) must be 55",          "check": "output_contains", "expected": "55"},
            {"description": "fib(1) must be 1",            "check": "output_contains", "expected": "1"},
            {"description": "Must print 10 lines",         "check": "min_line_count",  "expected": 10},
            {"description": "Must define function fib",    "check": "code_contains",   "expected": "def fib"},
        ]
    },

    # ── LESSON 12: Classes (Advanced) ─────────────────────────────────────
    "l12_e1": {
        "title": "Build a Dog Class",
        "lesson": 12,
        "description": "Create a class Dog with name and breed. Add a bark() method that prints '[name] says: Woof!'. Make 2 dogs and call bark() on each.",
        "starter": 'class Dog:\n    def __init__(self, name, breed):\n        pass  # save name and breed\n\n    def bark(self):\n        pass  # print the bark message\n\ndog1 = Dog("Rex",   "Labrador")\ndog2 = Dog("Bella", "Poodle")\ndog1.bark()\ndog2.bark()\n',
        "tests": [
            {"description": "Code must define a class",          "check": "code_contains",   "expected": "class Dog"},
            {"description": "Code must have __init__",           "check": "output_contains_any", "expected": ["Rex", "Bella"]},
            {"description": "Rex must bark",                     "check": "output_contains", "expected": "Rex"},
            {"description": "Bella must bark",                   "check": "output_contains", "expected": "Bella"},
            {"description": "Must print Woof",                   "check": "output_contains_any", "expected": ["Woof", "woof"]},
        ]
    },
    "l12_e2": {
        "title": "Bank Account",
        "lesson": 12,
        "description": "Create a BankAccount class with balance. Add deposit(amount) and withdraw(amount) methods. Print balance after each action.",
        "starter": 'class BankAccount:\n    def __init__(self, owner):\n        self.owner   = owner\n        self.balance = 0\n\n    def deposit(self, amount):\n        pass  # add to balance and print it\n\n    def withdraw(self, amount):\n        pass  # subtract from balance and print it\n\nacc = BankAccount("Alex")\nacc.deposit(100)\nacc.deposit(50)\nacc.withdraw(30)\n',
        "tests": [
            {"description": "Code must define class BankAccount",  "check": "code_contains",   "expected": "class BankAccount"},
            {"description": "After deposit 100+50, balance is 150","check": "output_contains", "expected": "150"},
            {"description": "After withdraw 30, balance is 120",   "check": "output_contains", "expected": "120"},
            {"description": "Must print at least 3 lines",         "check": "min_line_count",  "expected": 3},
        ]
    },
}

# ──────────────────────────────────────────────────────────────────────────
# SAFETY
# ──────────────────────────────────────────────────────────────────────────
BLOCKED = ["import os","import sys","import subprocess","import socket",
           "import urllib","import requests","__import__","open(","exec(","eval("]

def is_safe(code):
    for b in BLOCKED:
        if b in code:
            return False, b
    return True, None

def clean_error(text):
    text = re.sub(r'File ".*?", line (\d+)', r'Line \1', text)
    text = re.sub(r'  File.*\n', '', text)
    return text.strip()

# ──────────────────────────────────────────────────────────────────────────
# WS: JOIN — client registers its custom SID as a room
# ──────────────────────────────────────────────────────────────────────────
@socketio.on('join')
def handle_join(data):
    sid = data.get('sid', 'anon')
    join_room(sid)

# ──────────────────────────────────────────────────────────────────────────
# WS: RUN — real interactive terminal
# ──────────────────────────────────────────────────────────────────────────
@socketio.on('run_code')
def handle_run(data):
    sid  = data.get('sid', 'anon')
    code = data.get('code', '')

    safe, bad = is_safe(code)
    if not safe:
        emit('output', {'text': f"⛔ '{bad}' is not allowed.\n", 'type': 'error'})
        emit('run_done', {})
        return

    _kill_session(sid)

    # Detect turtle usage and keep the window open automatically
    uses_turtle = 'import turtle' in code or 'from turtle' in code
    run_code = code
    if uses_turtle and 'mainloop' not in code and 'turtle.done' not in code:
        run_code = code + '\nturtle.done()\n'

    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
    tmp.write(run_code); tmp.flush(); tmp.close()

    try:
        proc = subprocess.Popen(
            [sys.executable, '-u', tmp.name],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, bufsize=0,
        )
    except Exception as e:
        emit('output', {'text': str(e), 'type': 'error'})
        emit('run_done', {})
        return

    MAX_TOTAL_BYTES = 10_000   # 10 KB total output cap per run
    MAX_LINE_BYTES  = 500      # truncate any single line beyond 500 chars
    TIMEOUT_SECS    = 90 if uses_turtle else 60    # turtle windows stay open longer

    sessions[sid] = {
        'proc':       proc,
        'tmp':        tmp.name,
        'bytes_sent': 0,
        'line_len':   0,
    }

    def stream_stdout():
        sess = sessions.get(sid, {})
        try:
            for ch in iter(lambda: proc.stdout.read(1), ''):
                if sessions.get(sid) is None:
                    break
                sess['bytes_sent'] = sess.get('bytes_sent', 0) + len(ch)

                # ── total output cap ────────────────────────────────────
                if sess['bytes_sent'] > MAX_TOTAL_BYTES:
                    proc.kill()
                    socketio.emit('output', {
                        'text': (
                            '\n\n⛔ Too much output! Your program printed over 50 KB.\n'
                            '   This usually means an infinite loop printing non-stop.\n'
                            '   Tip: add a counter and stop after N lines.\n'
                        ),
                        'type': 'error'
                    }, to=sid)
                    break

                # ── per-line length cap ─────────────────────────────────
                if ch == '\n':
                    sess['line_len'] = 0
                    socketio.emit('output', {'text': ch, 'type': 'stdout'}, to=sid)
                else:
                    sess['line_len'] = sess.get('line_len', 0) + 1
                    if sess['line_len'] <= MAX_LINE_BYTES:
                        socketio.emit('output', {'text': ch, 'type': 'stdout'}, to=sid)
                    elif sess['line_len'] == MAX_LINE_BYTES + 1:
                        socketio.emit('output', {
                            'text': ' … [line too long, trimmed]',
                            'type': 'error'
                        }, to=sid)
                    # chars beyond limit are silently dropped
        except Exception:
            pass

    def stream_stderr():
        try:
            err = proc.stderr.read()
            if err:
                cleaned = clean_error(err)
                if len(cleaned) > 2000:
                    cleaned = cleaned[:2000] + '\n… [error output truncated]'
                socketio.emit('output',
                    {'text': '\n⚠️ ' + cleaned + '\n', 'type': 'error'}, to=sid)
        except Exception:
            pass

    def wait_proc():
        proc.wait()
        try: os.unlink(tmp.name)
        except: pass
        sessions.pop(sid, None)
        socketio.emit('run_done', {}, to=sid)

    def timeout_watchdog():
        import time
        time.sleep(TIMEOUT_SECS)
        if sid in sessions and sessions[sid]['proc'].poll() is None:
            sessions[sid]['proc'].kill()
            socketio.emit('output', {
                'text': (
                    f'\n\n⏱️ Time limit ({TIMEOUT_SECS}s) reached — program stopped.\n'
                    '   Tip: check for an infinite loop (while True: or a loop that never ends).\n'
                ),
                'type': 'error'
            }, to=sid)

    threading.Thread(target=stream_stdout,   daemon=True).start()
    threading.Thread(target=stream_stderr,   daemon=True).start()
    threading.Thread(target=wait_proc,       daemon=True).start()
    threading.Thread(target=timeout_watchdog,daemon=True).start()

# ──────────────────────────────────────────────────────────────────────────
# WS: SEND INPUT — student types in terminal
# ──────────────────────────────────────────────────────────────────────────
@socketio.on('send_input')
def handle_input(data):
    sid  = data.get('sid', 'anon')
    text = data.get('text', '') + '\n'
    sess = sessions.get(sid)
    if sess and sess['proc'].poll() is None:
        try:
            sess['proc'].stdin.write(text)
            sess['proc'].stdin.flush()
        except BrokenPipeError:
            pass

# ──────────────────────────────────────────────────────────────────────────
# WS: KILL
# ──────────────────────────────────────────────────────────────────────────
@socketio.on('kill_code')
def handle_kill(data):
    _kill_session(data.get('sid', 'anon'))
    emit('run_done', {})

def _kill_session(sid):
    sess = sessions.pop(sid, None)
    if sess:
        try: sess['proc'].kill()
        except: pass
        try: os.unlink(sess['tmp'])
        except: pass

# ──────────────────────────────────────────────────────────────────────────
# WS: SUBMIT — hidden tests
# ──────────────────────────────────────────────────────────────────────────
@socketio.on('submit_code')
def handle_submit(data):
    sid         = data.get('sid', 'anon')
    exercise_id = data.get('exercise_id', '')
    code        = data.get('code', '')

    ex = EXERCISES.get(exercise_id)
    if not ex:
        emit('submit_result', {'passed': False,
             'results': [{'desc': 'Unknown exercise', 'passed': False}]})
        return

    safe, bad = is_safe(code)
    if not safe:
        emit('submit_result', {'passed': False,
             'results': [{'desc': f"⛔ '{bad}' not allowed", 'passed': False}]})
        return

    inputs    = ex.get('inject_input', [])
    stdin_str = '\n'.join(inputs) + ('\n' if inputs else '')

    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
    tmp.write(code); tmp.flush(); tmp.close()

    try:
        r      = subprocess.run([sys.executable, tmp.name],
                                input=stdin_str, capture_output=True,
                                text=True, timeout=6)
        output = r.stdout.strip()
    except subprocess.TimeoutExpired:
        emit('submit_result', {'passed': False,
             'results': [{'desc': '⏱ Code timed out — check for infinite loops', 'passed': False}]})
        try: os.unlink(tmp.name)
        except: pass
        return
    finally:
        try: os.unlink(tmp.name)
        except: pass

    results  = []
    all_pass = True

    for test in ex.get('tests', []):
        chk    = test['check']
        desc   = test['description']
        passed = False

        if   chk == 'min_line_count':      lines = [l for l in output.splitlines() if l.strip()]; passed = len(lines) >= test['expected']
        elif chk == 'line_count':          lines = [l for l in output.splitlines() if l.strip()]; passed = len(lines) == test['expected']
        elif chk == 'all_lines_nonempty':  lines = output.splitlines(); passed = len(lines) >= 1 and all(l.strip() for l in lines if l)
        elif chk == 'output_contains':     passed = str(test['expected']).lower() in output.lower()
        elif chk == 'output_contains_any': passed = any(k.lower() in output.lower() for k in test['expected'])
        elif chk == 'code_contains':       passed = test['expected'] in code
        elif chk == 'contains_input':
            idx = test.get('input_index', 0)
            passed = inputs[idx].lower() in output.lower() if idx < len(inputs) else True
        else: passed = True

        results.append({'desc': desc, 'passed': passed})
        if not passed: all_pass = False

    emit('submit_result', {'passed': all_pass, 'results': results, 'output': output})

# ──────────────────────────────────────────────────────────────────────────
# HTTP
# ──────────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/playground')
def playground():
    return send_from_directory('static', 'playground.html')

@app.route('/api/exercises')
def get_exercises():
    return jsonify({
        eid: {'title': ex['title'], 'lesson': ex['lesson'],
              'description': ex['description'], 'starter': ex['starter']}
        for eid, ex in EXERCISES.items()
    })

# ──────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--host', action='store_true',
                   help='Accept connections from other devices (classroom mode)')
    args = p.parse_args()

    # Cloud platforms (Railway, Render) set PORT env var; fall back to 5000 locally
    port = int(os.environ.get('PORT', 5000))
    # Always bind to 0.0.0.0 when PORT env var is set (cloud deployment)
    host = '0.0.0.0' if (args.host or 'PORT' in os.environ) else '127.0.0.1'

    print("🐍  Python Kids Server starting...")
    if host == '0.0.0.0':
        print("🌐  Classroom mode ON — students can connect from other devices")
        print("    Find your IP:  ipconfig (Windows) | ifconfig (Mac/Linux)")
        print(f"    Students visit:  http://YOUR_IP:{port}")
    else:
        print(f"📡  Open: http://localhost:{port}")
    print("    Ctrl+C to stop\n")
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
