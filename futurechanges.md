# Future Enhancements

## Parallel Execution of AI Audits
**Goal:** Run deep research for all selected stocks simultaneously rather than sequentially, vastly speeding up the audit phase, while keeping the live WebSocket log stream intact.

**Technical Architecture:**
1. **Celery Groups & Chords:** 
   Currently, `run_research_task` uses a single `for` loop to research stocks one by one. We will convert this into a "Master-Worker" pattern using Celery's `group` primitive.
   - The master task (`run_research_task`) will spawn $N$ child tasks (e.g., `audit_single_stock_task.delay(ticker)`).
   - Because Celery workers run concurrently, all $N$ stocks will hit the LLM APIs at the same time in parallel.

2. **WebSocket Log Aggregation:**
   - To keep the frontend simple, we won't open $N$ different WebSockets. 
   - Instead, we will pass the `master_task_id` down to every child task as an argument.
   - When a child task generates a log (e.g., "Extracting fundamentals for CANBK..."), it will push the log to the `master_task_id` Redis channel.
   - The React frontend will continue listening to the single master WebSocket, and it will see an interleaved, blazing-fast stream of logs coming from all the parallel workers simultaneously.

3. **Coordination (Celery Chord):**
   - We will use a Celery `chord` to wait for all parallel child tasks to finish. Once the last child finishes, a callback task will fire to mark the overall `ResearchRun` status as `SUCCESS` and notify the frontend that the batch is complete.
