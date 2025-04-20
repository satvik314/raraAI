from datetime import datetime 
from typing import List, Optional
from zoneinfo import ZoneInfo
import os

from agno.agent import Agent, RunResponse  
from agno.models.google import Gemini
from pydantic import BaseModel, Field, field_validator
from rich.pretty import pprint  
from dotenv import load_dotenv
import supabase

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")


task_categories = {
    # ── Core revenue engines ─────────────────────────────────────────────
    "Gen_AI_Course": "Curriculum design, cohort delivery, learner support, continuous syllabus updates.",
    "Corporate_Training": "Enterprise workshops: scoping, slide prep, demos, feedback & reporting.",
    "Consulting": "Advisory projects for firms adopting Gen‑AI; solution design, stakeholder calls.",
    "SaaS_Projects": "Internal product road‑maps (e.g., BuildFast Studio); coding sprints, QA, releases.",
    "Educhain": "Open‑source maintenance, issue triage, version bumps, community pull‑request reviews.",

    # ── Growth & community ───────────────────────────────────────────────
    "Content_Creation": "All social posts (LinkedIn, X, YT), newsletters, podcasts, slide teasers.",
    "Community_and_Events": "Weekly meet‑ups, Discord moderation, speaker coordination, sponsorships.",

    # ── External acceleration ────────────────────────────────────────────
    "Business_Development": "Strategic partnerships, channel alliances, enterprise pipeline, deal negotiation.",

    # ── Internal excellence ──────────────────────────────────────────────
    "R_and_D": "Model experiments, agent prototypes, benchmarking new frameworks—future bets.",
    "People_Ops": "Hiring, onboarding, performance, culture programmes, retention initiatives.",
    "Team_Tasks": "Assign & track deliverables for specific team‑members or pods.",
    "General_Admin": "Accounting, invoicing, taxes, legal docs, vendor & office logistics (formerly 'Compliance/F&A').",
    "Personal_Development": "Learning, conferences, networking, health & well‑being routines."
}

# Helper function for ordinal date suffix
def get_ordinal_suffix(day):
    if 11 <= day <= 13:
        return 'th'
    suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
    return suffixes.get(day % 10, 'th')

# Helper function to format datetime
def format_datetime_readable(dt):
    if not isinstance(dt, datetime):
        return str(dt)
    day = dt.day
    suffix = get_ordinal_suffix(day)
    return dt.strftime(f"{day}{suffix} %B, %a, %Y, %-I.%M%p")

# Helper function to format date only
def format_date_readable(date_str):
    if not date_str or date_str == "none":
        return "None"
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day = dt.day
        suffix = get_ordinal_suffix(day)
        return dt.strftime(f"{day}{suffix} %B, %a, %Y")
    except ValueError:
        return date_str

class TaskDetails(BaseModel):
    task_description: str = Field(..., description="The original description of the task provided by the user.")
    category: str = Field(
        ..., 
        description=f"The most relevant category for the task based on the following options: {list(task_categories.keys())}. Use the descriptions provided here: {task_categories}"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo("Asia/Kolkata")), 
        description="The date and time when the task was saved (IST)."
    )
    tags: List[str] = Field(
        default_factory=list, 
        description="A list of relevant keywords or tags (like people's names, company names, project codes) extracted from the task description."
    )
    deadline: str = Field(
        description="The deadline date in YYYY-MM-DD format (e.g., '2025-04-25') or 'none' if no deadline exists."
    )
    # Remove the id field from the model since it's causing issues with Gemini

    @field_validator('category')
    def category_must_be_in_list(cls, v):
        if v not in task_categories:
            raise ValueError(f"Category '{v}' is not a valid category. Choose from: {list(task_categories.keys())}")
        return v
        
    def save_to_db(self, supabase_client, test_mode=False):
        """Save the task to the Supabase database.
        
        Args:
            supabase_client: The Supabase client to use for the database operation.
            test_mode: If True, save to the tasks_test table. If False, save to the tasks table.
        
        Returns:
            The ID of the inserted task if successful, None otherwise.
        """
        # Convert deadline 'none' to None for database
        deadline_value = None if self.deadline.lower() == 'none' else self.deadline
        
        # Insert the task into the database
        data = {
            "task_description": self.task_description,
            "category": self.category,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "deadline": deadline_value
        }
        
        # Choose the appropriate table based on test_mode
        table_name = 'tasks_test' if test_mode else 'tasks'
        
        result = supabase_client.table(table_name).insert(data).execute()
        
        # Return the ID if the insert was successful
        if result.data and len(result.data) > 0:
            task_id = result.data[0]['id']
            return task_id
        return None

# Initialize Supabase client
def get_supabase_client():
    """Initialize and return a Supabase client."""

    # You can also use environment variables
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    return supabase.create_client(url, key)

tasksaver_agent = Agent(
    model=Gemini(id="gemini-2.0-flash"), 
    description="""You are a task assistant. Given a task description and the current timestamp, perform the following actions:
    1. Categorize the task into one of the predefined categories
    2. Extract relevant keywords/tags (names, companies, projects, tools)
    3. If a deadline is mentioned, calculate the specific DATE ONLY and return it in YYYY-MM-DD format
    4. If no deadline is mentioned, return 'none' (lowercase) for the deadline field
    5. Record all task details accurately
    
    Rules for deadline calculation:
    - For relative deadlines ('in 3 days', 'next week'), calculate the date based on the current timestamp
    - For specific dates ('May 1st', '30th December'), include the proper year based on the current timestamp
    - For terms like 'EOD', 'by midnight', just return the date part
    - For terms like 'tomorrow', return the next day's date
    - Always return date in YYYY-MM-DD format
    - If no deadline mentioned, return 'none' (lowercase)
    """,
    response_model=TaskDetails,
    add_datetime_to_instructions=True,
)

def process_task(task_phrase, test_mode=False):
    """Process a task phrase and save it to the Supabase database.
    
    Args:
        task_phrase: The task phrase to process.
        test_mode: If True, save to the tasks_test table. If False, save to the tasks table.
    
    Returns:
        The processed task details if successful, None otherwise.
    """
    response = tasksaver_agent.run(task_phrase)
    
    if isinstance(response.content, TaskDetails):
        task_data = response.content.model_dump()
        
        # Print task details
        print("Task processed successfully!")
        print(f"  Description: {task_data['task_description']}")
        print(f"  Category: {task_data['category']}")
        print(f"  Tags: {', '.join(task_data['tags']) if task_data['tags'] else 'None'}")
        
        # Format the deadline date if it exists and is not 'none'
        formatted_deadline = format_date_readable(task_data['deadline'])
        print(f"  Deadline: {formatted_deadline}")
        
        formatted_time = format_datetime_readable(task_data['timestamp'])
        print(f"  Timestamp: {formatted_time}")
        
        # Save to Supabase
        try:
            supabase_client = get_supabase_client()
            task_id = response.content.save_to_db(supabase_client, test_mode=test_mode)
            
            # Determine which table was used
            table_name = 'tasks_test' if test_mode else 'tasks'
            
            if task_id:
                print(f"  \u2705 Task saved to {table_name} with ID: {task_id}")
            else:
                print(f"  \u274c Failed to save task to {table_name}")
        except Exception as e:
            print(f"  \u274c Error saving to database: {str(e)}")
        
        return response.content
    else:
        print("Error: Agent did not return the expected TaskDetails structure.")
        print("Raw response:", response.content)
        return None

# # Example usage
# if __name__ == "__main__":
#     # task_phrase = "Prepare the slides for Generative AI Course by 25th April midnight"
#     task_phrase = "Prepare the slides for Generative AI Course in 3 days."
#     task = process_task(task_phrase)