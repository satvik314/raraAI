import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Set environment variables from Streamlit secrets before importing tasksaver
os.environ["SUPABASE_URL"] = st.secrets["SUPABASE_URL"]
os.environ["SUPABASE_KEY"] = st.secrets["SUPABASE_KEY"]
os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

# Now import from tasksaver after setting environment variables
from tasksaver import process_task, get_supabase_client, format_date_readable

# Set page config
st.set_page_config(
    page_title="raraAI Task Manager",
    page_icon="✅",
    layout="wide"
)

# Initialize session state variables if they don't exist
if 'refresh_data' not in st.session_state:
    st.session_state.refresh_data = True

# Function to fetch tasks from Supabase
def fetch_tasks(test_mode=False):
    try:
        supabase = get_supabase_client()
        table_name = 'tasks_test' if test_mode else 'tasks'
        response = supabase.table(table_name).select('*').order('id', desc=True).execute()
        
        if response.data:
            return response.data
        return []
    except Exception as e:
        st.error(f"Error fetching tasks: {str(e)}")
        return []

# Function to format tasks for display
def format_tasks_for_display(tasks):
    if not tasks:
        return pd.DataFrame()
    
    # Create a DataFrame
    df = pd.DataFrame(tasks)
    
    # Format the timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%d %b %Y, %I:%M %p')
    
    # Format the deadline
    if 'deadline' in df.columns:
        df['deadline'] = df['deadline'].apply(lambda x: format_date_readable(x) if x else 'None')
    
    # Format tags as comma-separated string
    if 'tags' in df.columns:
        df['tags'] = df['tags'].apply(lambda x: ', '.join(x) if x else 'None')
    
    return df

# Main app
def main():
    st.title("raraAI Task Manager")
    
    # Create tabs
    tab1, tab2 = st.tabs(["Add Task", "View Tasks"])
    
    # Tab 1: Add Task
    with tab1:
        st.header("Add a New Task")
        
        # Task input
        task_input = st.text_area("Enter your task description:", 
                               placeholder="Example: Create slides for Module 6 of the Gen AI course by next Tuesday",
                               height=100)
        
        # Mode selection
        col1, col2 = st.columns(2)
        with col1:
            test_mode = st.checkbox("Test Mode", value=False, 
                                 help="If checked, tasks will be saved to the test database")
        
        # Submit button
        if st.button("Process Task", type="primary"):
            if task_input.strip():
                with st.spinner("Processing task..."):
                    task = process_task(task_input, test_mode=test_mode)
                    if task:
                        st.success("Task processed and saved successfully!")
                        st.session_state.refresh_data = True
                    else:
                        st.error("Failed to process task.")
            else:
                st.warning("Please enter a task description.")
    
    # Tab 2: View Tasks
    with tab2:
        st.header("View Tasks")
        
        # Mode selection for viewing
        view_test_mode = st.checkbox("View Test Database", value=False, 
                                  help="If checked, tasks from the test database will be displayed")
        
        # Refresh button
        if st.button("Refresh Data") or st.session_state.refresh_data:
            st.session_state.refresh_data = False
            with st.spinner("Loading tasks..."):
                tasks = fetch_tasks(test_mode=view_test_mode)
                df = format_tasks_for_display(tasks)
                
                if not df.empty:
                    # Reorder columns for better display
                    columns_order = ['id', 'task_description', 'category', 'deadline', 'tags', 'timestamp']
                    display_df = df[columns_order]
                    
                    # Rename columns for better display
                    display_df = display_df.rename(columns={
                        'id': 'ID',
                        'task_description': 'Task Description',
                        'category': 'Category',
                        'deadline': 'Deadline',
                        'tags': 'Tags',
                        'timestamp': 'Created At'
                    })
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        column_config={
                            "Task Description": st.column_config.TextColumn(
                                width="large",
                            ),
                        },
                        hide_index=True,
                    )
                    
                    # Display task count
                    st.caption(f"Total tasks: {len(display_df)}")
                else:
                    st.info(f"No tasks found in the {'test' if view_test_mode else 'production'} database.")

if __name__ == "__main__":
    main()