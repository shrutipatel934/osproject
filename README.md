# Advanced Hybrid Scheduler

A CPU scheduling simulator implementing a hybrid approach combining:
- Priority-based preemptive scheduling
- Aging mechanism to prevent starvation
- Round Robin queue for long-waiting processes

## Setup
\`\`\`bash
pip install -r requirements.txt
python app.py
\`\`\`

Visit http://localhost:5000

## Configuration
- AGING_THRESHOLD: 8 time units
- RR_WAIT_THRESHOLD: 10 time units  
- TIME_QUANTUM: 4 time units
