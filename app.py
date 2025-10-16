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

def hybrid_scheduler(processes, priority_rule):
    """Implements the advanced hybrid scheduler with improved aging."""
    current_time = 0
    completed_processes = 0
    n = len(processes)
    gantt_chart = []
    events = []
    
    priority_queue = []
    rr_queue = deque()
    
    processes.sort(key=lambda p: p.arrival_time)
    process_idx = 0
    
    last_run_pid = -1

    while completed_processes < n:
        # Step 1: Process Arrival
        while process_idx < n and processes[process_idx].arrival_time <= current_time:
            priority_queue.append(processes[process_idx])
            events.append({
                'time': current_time,
                'type': 'arrival',
                'pid': processes[process_idx].pid,
                'message': f'P{processes[process_idx].pid} arrived'
            })
            process_idx += 1

        # Move long-waiting processes to RR queue
        remaining_in_priority_queue = []
        for p in priority_queue:
            if p.total_wait_time >= RR_WAIT_THRESHOLD and not p.is_in_rr_queue:
                p.is_in_rr_queue = True
                rr_queue.append(p)
                events.append({
                    'time': current_time,
                    'type': 'rr_move',
                    'pid': p.pid,
                    'message': f'P{p.pid} moved to RR queue due to long wait'
                })
            else:
                remaining_in_priority_queue.append(p)
        priority_queue = remaining_in_priority_queue

        # Step 2: Select Process to Run
        process_to_run = None
        if priority_queue:
            if priority_rule == '1':
                sort_key = lambda p: (p.current_priority, p.remaining_time)
            else:
                sort_key = lambda p: (-p.current_priority, p.remaining_time)
            
            priority_queue.sort(key=sort_key)
            process_to_run = priority_queue[0]
        elif rr_queue:
            process_to_run = rr_queue[0]

        if process_to_run is None:
            current_time += 1
            continue

        # Step 3: Handle Preemption & Quantum
        if last_run_pid != process_to_run.pid:
            process_to_run.quantum_used = 0
            if last_run_pid != -1:
                last_p = next((p for p in rr_queue if p.pid == last_run_pid), None)
                if last_p: rr_queue.rotate(-1)

        # Execute process
        if process_to_run.start_time == -1:
            process_to_run.start_time = current_time
            process_to_run.response_time = current_time - process_to_run.arrival_time
        
        gantt_chart.append({
            'pid': process_to_run.pid,
            'start': current_time,
            'end': current_time + 1
        })
        process_to_run.remaining_time -= 1

        current_time += 1
        last_run_pid = process_to_run.pid

        # Handle Round Robin quantum
        if process_to_run.is_in_rr_queue:
            process_to_run.quantum_used += 1
            if process_to_run.quantum_used >= TIME_QUANTUM:
                rr_queue.rotate(-1)
                process_to_run.quantum_used = 0
                last_run_pid = -1

        # Check for completion
        if process_to_run.remaining_time == 0:
            process_to_run.is_completed = True
            process_to_run.completion_time = current_time
            completed_processes += 1
            last_run_pid = -1
            events.append({
                'time': current_time,
                'type': 'completion',
                'pid': process_to_run.pid,
                'message': f'P{process_to_run.pid} completed'
            })
            if process_to_run.is_in_rr_queue:
                if rr_queue and rr_queue[0].pid == process_to_run.pid:
                    rr_queue.popleft()
            else:
                if priority_queue and priority_queue[0].pid == process_to_run.pid:
                    priority_queue.pop(0)

        # Step 4: Aging for all WAITING processes
        for p in priority_queue + list(rr_queue):
            if not p.is_completed and p.pid != process_to_run.pid:
                p.total_wait_time += 1
                p.wait_time_since_last_boost += 1
                if p.wait_time_since_last_boost >= AGING_THRESHOLD:
                    if priority_rule == '1':
                        if p.current_priority > 1:
                            p.current_priority -= 1
                            events.append({
                                'time': current_time,
                                'type': 'aging',
                                'pid': p.pid,
                                'message': f'P{p.pid} priority boosted to {p.current_priority}'
                            })
                            p.wait_time_since_last_boost = 0
                    else:
                        p.current_priority += 1
                        events.append({
                            'time': current_time,
                            'type': 'aging',
                            'pid': p.pid,
                            'message': f'P{p.pid} priority boosted to {p.current_priority}'
                        })
                        p.wait_time_since_last_boost = 0
    
    # Calculate metrics
    processes.sort(key=lambda p: p.pid)
    metrics = []
    total_wt, total_tat, total_rt = 0, 0, 0
    
    for p in processes:
        turnaround_time = p.completion_time - p.arrival_time
        waiting_time = turnaround_time - p.burst_time
        total_tat += turnaround_time
        total_wt += waiting_time
        total_rt += p.response_time
        
        metrics.append({
            'pid': p.pid,
            'arrival_time': p.arrival_time,
            'burst_time': p.burst_time,
            'priority': p.original_priority,
            'completion_time': p.completion_time,
            'turnaround_time': turnaround_time,
            'waiting_time': waiting_time,
            'response_time': p.response_time
        })
    
    averages = {
        'avg_tat': total_tat / n,
        'avg_wt': total_wt / n,
        'avg_rt': total_rt / n
    }
    
    return {
        'gantt_chart': gantt_chart,
        'metrics': metrics,
        'averages': averages,
        'events': events
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/schedule', methods=['POST'])
def schedule():
    try:
        data = request.json
        processes_data = data.get('processes', [])
        priority_rule = data.get('priority_rule', '1')
        
        if not processes_data:
            return jsonify({'error': 'No processes provided'}), 400
        
        processes = []
        for p in processes_data:
            processes.append(Process(
                pid=p['pid'],
                arrival_time=p['arrival_time'],
                burst_time=p['burst_time'],
                priority=p['priority']
            ))
        
        result = hybrid_scheduler(processes, priority_rule)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
