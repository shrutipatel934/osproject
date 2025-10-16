import sys
from collections import deque

# --- Configuration Constants ---
AGING_THRESHOLD = 8       # Every 8 total wait ticks, priority increases.
RR_WAIT_THRESHOLD = 10    # If total wait > 10, move to the RR queue.
TIME_QUANTUM = 4          # Time quantum for the Round Robin queue.

class Process:
    """Represents a process with all necessary attributes for complex scheduling."""
    def __init__(self, pid, arrival_time, burst_time, priority):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.original_priority = priority
        
        # --- Dynamic State Variables ---
        self.current_priority = priority
        self.remaining_time = burst_time
        self.start_time = -1
        self.completion_time = 0
        self.is_completed = False
        
        # --- Metrics and Aging ---
        self.total_wait_time = 0
        self.wait_time_since_last_boost = 0
        self.response_time = -1
        self.is_in_rr_queue = False
        self.quantum_used = 0

def print_gantt_chart(gantt):
    """Prints a detailed Gantt chart showing process execution over time."""
    if not gantt: return
    print("\n📊 Gantt Chart")
    print("-" * 50)
    current_pid = -1
    start_time = 0
    for pid, time in gantt:
        if pid != current_pid:
            if current_pid != -1:
                print(f"| {start_time}-{time}: P{current_pid} ", end="")
            start_time = time
            current_pid = pid
    if gantt:
        print(f"| {start_time}-{gantt[-1][1] + 1}: P{current_pid} |")
    print("-" * 50)

def print_results(processes, total_time):
    """Calculates and prints all performance metrics."""
    n = len(processes)
    if n == 0: return

    total_wt, total_tat, total_rt = 0, 0, 0
    processes.sort(key=lambda p: p.pid)

    print("\n📊 Performance Metrics")
    print("-" * 80)
    print("PID\tAT\tBT\tPri\tCT\tTAT\tWT\tRT")
    print("-" * 80)
    for p in processes:
        turnaround_time = p.completion_time - p.arrival_time
        waiting_time = turnaround_time - p.burst_time
        total_tat += turnaround_time
        total_wt += waiting_time
        total_rt += p.response_time
        
        print(f"{p.pid}\t{p.arrival_time}\t{p.burst_time}\t{p.original_priority}\t"
              f"{p.completion_time}\t{turnaround_time}\t{waiting_time}\t{p.response_time}")
    
    print("-" * 80)
    print(f"Average Turnaround Time (ATT): {total_tat / n:.2f}")
    print(f"Average Waiting Time (AWT):    {total_wt / n:.2f}")
    print(f"Average Response Time:         {total_rt / n:.2f}")

# MODIFIED: Function now takes the priority_rule as an argument
def hybrid_scheduler(processes, priority_rule):
    """Implements the advanced hybrid scheduler with improved aging."""
    current_time = 0
    completed_processes = 0
    n = len(processes)
    gantt_chart = []
    
    priority_queue = []
    rr_queue = deque()
    
    processes.sort(key=lambda p: p.arrival_time)
    process_idx = 0
    
    last_run_pid = -1

    while completed_processes < n:
        # Step 1: Process Arrival
        while process_idx < n and processes[process_idx].arrival_time <= current_time:
            priority_queue.append(processes[process_idx])
            process_idx += 1

        # Move long-waiting processes to RR queue
        remaining_in_priority_queue = []
        for p in priority_queue:
            if p.total_wait_time >= RR_WAIT_THRESHOLD and not p.is_in_rr_queue:
                p.is_in_rr_queue = True
                rr_queue.append(p)
                print(f"🕒 (Time {current_time}) P{p.pid} moved to RR queue due to long wait.")
            else:
                remaining_in_priority_queue.append(p)
        priority_queue = remaining_in_priority_queue

        # Step 2: Select Process to Run
        process_to_run = None
        if priority_queue:
            # MODIFIED: Sorting logic now depends on the priority_rule
            if priority_rule == '1':
                # Lower number = higher priority
                sort_key = lambda p: (p.current_priority, p.remaining_time)
            else:
                # Higher number = higher priority (use negative for descending sort)
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
        
        gantt_chart.append((process_to_run.pid, current_time))
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
                    
                    # MODIFIED: Aging logic now depends on the priority_rule
                    if priority_rule == '1':
                        if p.current_priority > 1: # Don't go below 1
                            p.current_priority -= 1
                            print(f"✨ (Time {current_time}) P{p.pid} priority boosted to {p.current_priority} due to aging.")
                            p.wait_time_since_last_boost = 0
                    else: # '2'
                        # For higher-is-better, just keep increasing priority
                        p.current_priority += 1
                        print(f"✨ (Time {current_time}) P{p.pid} priority boosted to {p.current_priority} due to aging.")
                        p.wait_time_since_last_boost = 0
    
    # Step 6: Compute and display metrics
    print_gantt_chart(gantt_chart)
    print_results(processes, current_time)

if __name__ == "__main__":
    
    # --- NEW: Ask for priority rule ---
    priority_rule = ''
    while priority_rule not in ['1', '2']:
        print("Please choose the priority rule:")
        print("  1: Lower number means HIGHER priority")
        print("  2: Higher number means HIGHER priority")
        priority_rule = input("Enter your choice (1 or 2): ")
        if priority_rule not in ['1', '2']:
            print("Invalid choice. Please enter only 1 or 2.\n")
    
    # --- A sample set of processes is now used instead of user input ---
    processes = [
        Process(pid=1, arrival_time=0, burst_time=8, priority=3), # Will age and move to RR
        Process(pid=2, arrival_time=2, burst_time=4, priority=2),
        Process(pid=3, arrival_time=4, burst_time=2, priority=1), # High priority, will preempt
        Process(pid=4, arrival_time=5, burst_time=6, priority=2),
        Process(pid=5, arrival_time=15, burst_time=5, priority=1) # Arrives late to show more preemption
    ]
    print("\n🚀 Advanced Hybrid Scheduler - Running with sample data...")
    print("-" * 40)
    # MODIFIED: Pass the rule to the scheduler
    hybrid_scheduler(processes, priority_rule)


    # --- User Input Section HAS BEEN COMMENTED OUT ---
    '''
    processes = []
    print("🚀 Advanced Hybrid Scheduler - User Input")
    print("-" * 40)
    
    try:
        num_processes = int(input("Enter the total number of processes: "))
        if num_processes <= 0:
            print("Number of processes must be positive.")
        else:
            # MODIFIED: This prompt string would be set based on the rule
            if priority_rule == '1':
                priority_prompt = "  Priority for P{pid} (lower number = higher priority): "
            else:
                priority_prompt = "  Priority for P{pid} (higher number = higher priority): "
                
            for i in range(num_processes):
                print(f"\n--- Enter details for Process {i+1} ---")
                pid = i + 1
                arrival = int(input(f"  Arrival Time for P{pid}: "))
                burst = int(input(f"  Burst Time for P{pid}: "))
                # Use the dynamic prompt
                priority = int(input(priority_prompt.format(pid=pid)))

                if burst <= 0:
                    print("Error: Burst time must be greater than zero.")
                    break
                if arrival < 0 or priority <= 0:
                    print("Error: Arrival time and priority must be positive.")
                    break
                
                processes.append(Process(pid, arrival, burst, priority))
            
            if len(processes) == num_processes:
                print("\n✅ All processes entered. Starting scheduler...")
                print("-" * 40)
                # Pass the rule to the scheduler
                hybrid_scheduler(processes, priority_rule)

    except ValueError:
        print("\n❌ Error: Invalid input. Please enter integers only.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    '''
