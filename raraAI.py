from tasksaver import process_task, format_datetime_readable
import sys
import os

# There are multiple ways to enable test mode:
# 1. Command line argument: python3 raraAI.py --test
# 2. Environment variable: export RARA_TEST_MODE=1 (then run python3 raraAI.py)
# 3. Directly set the variable below

# Set to True to always use test mode, False to always use production mode
# or None to determine from command line args or environment variables
OVERRIDE_TEST_MODE = None
# OVERRIDE_TEST_MODE = False

# Check if test mode is enabled
test_mode = OVERRIDE_TEST_MODE if OVERRIDE_TEST_MODE is not None else (
    '--test' in sys.argv or 
    os.getenv('RARA_TEST_MODE') == '1'
)

# Example task
# task_phrase = "Create a Twitter post on Gen AI Course starting on May 3rd. It should be done today."
task_phrase = "Create a consulting proposal for SUTRA by Thursday. "

# Process the task and save it to Supabase
# If running with --test flag, it will save to the tasks_test table
# Otherwise, it will save to the production tasks table
print(f"Running in {'TEST' if test_mode else 'PRODUCTION'} mode")
task = process_task(task_phrase, test_mode=test_mode)

# The task is now saved to the Supabase database in either:
# - 'tasks_test' table if test_mode=True
# - 'tasks' table if test_mode=False
#
# Sample output in the database will be:
# task_description='Create a LinkedIn post on Gen AI Course starting on May 3rd. It should be done today.'
# category='Content_Creation'
# timestamp=datetime.datetime(2025, 4, 20, 19, 13, 50, 123456, tzinfo=TzInfo(UTC))
# tags=['LinkedIn', 'Gen AI Course']
# deadline='2025-04-20'

