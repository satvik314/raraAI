from agno.agent import Agent
from agno.models.google import Gemini

def create_linkedin_post_agent(topic):
    prompt_template = """
    # You are a content writer for Satvik Paramkusham, Founder of Build Fast with AI.

    Write a LinkedIn post on the topic: {}

    The post should follow Satvik's distinctive writing style, which includes:

    1. Opening with an attention-grabbing statement, often using emojis like 🚀, 🤯, or 🔥
    2. Using short, impactful paragraphs with 1-3 sentences each
    3. Including numbered or bulleted points (often with emoji numbers like 1️⃣, 2️⃣, 3️⃣)
    4. Adding technical details and insights that showcase expertise
    5. Often using the wavy line emoji (〰️) as bullet points within numbered sections
    6. Including personal reflections or experiences when relevant
    # 7. Ending with a call to action, often related to Build Fast with AI's courses or workshops
    8. Using hashtags at the end

    Make the post informative, enthusiastic, and engaging - focusing on practical applications of AI technology.
    """.format(topic)

    agent = Agent(
        model=Gemini(
            id="gemini-2.0-flash",
            grounding=True
        ),
        add_datetime_to_instructions=True,
    )

    response = agent.run(prompt_template)
    return response



def create_tweet_agent(topic):
    prompt_template = """
    # You are a tweet writer for the latest news on Generative AI.

    Write a tweet on the topic: {}

    Format:
    - Attention-grabbing headline about the update
    - 1-2 sentence paragraph
    - 3-4 bullet pointers each starting with 〰️
    - Conclusion with insightful commentary

    Guidelines:
    - Stay within Twitter's character limit
    - Keep bullet points and sentences short and sweet
    - Don't be too formal
    - Be direct and avoid generic phrases like "new benchmarks with its massive scale and impressive capabilities"
    - Don't include reference links
    """.format(topic)

    agent = Agent(
        model=Gemini(
            id="gemini-2.0-flash",
            grounding=True
        ),
        add_datetime_to_instructions=True,
    )

    response = agent.run(prompt_template)
    return response


