from datetime import datetime 
from typing import List
from zoneinfo import ZoneInfo

from agno.agent import Agent, RunResponse  
from agno.models.google import Gemini
from pydantic import BaseModel, Field, field_validator
from rich.pretty import pprint  
from dotenv import load_dotenv

load_dotenv()

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

    @field_validator('category')
    def category_must_be_in_list(cls, v):
        if v not in task_categories:
            raise ValueError(f"Category '{v}' is not a valid category. Choose from: {list(task_categories.keys())}")
        return v

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

# task_phrase = "Prepare the slides for Generative AI Course by 25th April midnight"
task_phrase = "Prepare the slides for Generative AI Course in 3 days."
response = tasksaver_agent.run(task_phrase)

if isinstance(response.content, TaskDetails):
    print("Task saved successfully!")
    task_data = response.content.model_dump()
    
    print(f"  Description: {task_data['task_description']}")
    print(f"  Category: {task_data['category']}")
    print(f"  Tags: {', '.join(task_data['tags']) if task_data['tags'] else 'None'}")
    
    # Format the deadline date if it exists and is not 'none'
    formatted_deadline = format_date_readable(task_data['deadline'])
    print(f"  Deadline: {formatted_deadline}")
    
    formatted_time = format_datetime_readable(task_data['timestamp'])
    print(f"  Timestamp: {formatted_time}")
else:
    print("Error: Agent did not return the expected TaskDetails structure.")
    print("Raw response:", response.content)