 # Hybrid Scheduler
 
 Priority-Based Scheduling with Aging and Round Robin
 
 A small CPU scheduling simulator that combines a priority-based scheduler with an aging mechanism to avoid starvation and a Round Robin queue for processes that wait too long.
 
 ## Features
 
 - Priority-based preemptive scheduling
 - Aging to gradually increase priority for long-waiting processes
 - Round Robin queue for fair time-sharing of long-waiting processes
 - Simple web UI (served by `app.py`) to visualize scheduling
 
 ## Requirements
 
 - Python 3.8+
 - See `requirements.txt` for Python dependencies
 
 ## Quick start
 
 Install dependencies and run the app:
 
 ```bash
 pip install -r requirements.txt
 python app.py
 ```
 
 Open your browser at http://localhost:5000 to view the simulator.
 
 ## Configuration
 
 You can adjust scheduling parameters in the code or configuration (if provided):
 
 - `TIME_QUANTUM` — time slice for Round Robin
 - `AGING_THRESHOLD` — how long a process waits before aging increments
 - `RR_WAIT_THRESHOLD` — wait time before moving a process to the RR queue
 
 ## Contributors
 
 - Shruti Patel
 - Aanal Joshi
 
 ## License
 
 This project is provided as-is for learning and demonstration purposes.

