#!/bin/bash
PID=$1
echo "Waiting for process $PID to complete..."
wait $PID
echo "Process $PID completed."
echo "Running upload script..."
./.venv/bin/python upload_to_sheets.py
echo "Done."
