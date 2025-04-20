from tasksaver import tasksaver_agent, TaskDetails, format_datetime_readable


task_phrase = "Create slides and videos for Module 6 for the Gen AI course"
response = tasksaver_agent.run(task_phrase)

if isinstance(response.content, TaskDetails):
    print("Task saved successfully!")
    task_data = response.content.model_dump() 
    print(f"  Description: {task_data['task_description']}")
    print(f"  Category: {task_data['category']}")
    print(f"  Tags: {', '.join(task_data['tags']) if task_data['tags'] else 'None'}")
    # Format the timestamp before printing
    formatted_time = format_datetime_readable(task_data['timestamp'])
    print(f"  Timestamp: {formatted_time}")
else:
    print("Error: Agent did not return the expected TaskDetails structure.")
    print("Raw response:", response.content)
