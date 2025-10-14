from flask import Flask, render_template, request, jsonify
from collections import deque

app = Flask(__name__)

# --- Configuration Constants ---
AGING_THRESHOLD = 8
RR_WAIT_THRESHOLD = 10
TIME_QUANTUM = 4

class Process:
    """Represents a process with all necessary attributes for complex scheduling."""
    def __init__(self, pid, arrival_time, burst_time, priority):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.original_priority = priority
        
        self.current_priority = priority
        self.remaining_time = burst_time
        self.start_time = -1
        self.completion_time = 0
        self.is_completed = False
        
        self.total_wait_time = 0
        self.wait_time_since_last_boost = 0
        self.response_time = -1
        self.is_in_rr_queue = False
        self.quantum_used = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/schedule', methods=['POST'])
def schedule():
    return jsonify({'error': 'Not implemented yet'}), 501

if __name__ == '__main__':
    app.run(debug=True, port=5000)
