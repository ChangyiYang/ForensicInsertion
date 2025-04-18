from langchain.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import ast
import json

# --- Helper function ---
def escape_braces(s: str) -> str:
    """Escape curly braces to avoid format errors inside PromptTemplate."""
    return s.replace("{", "{{").replace("}", "}}")

def format_examples(examples_raw):
    """Format few-shot examples: dict -> escaped string."""
    formatted = []
    for ex in examples_raw:
        formatted.append({
            "activity": ex["activity"],
            "queries": escape_braces(json.dumps(ex["queries"], indent=2))
        })
    return formatted

# --- Few-shot examples ---
examples_raw = [
    {
        "activity": "I was reading about climate change and polar bears",
        "queries": {
            "documents": ["effects of climate change", "polar bear habitat loss"],
            "images": ["polar bears on melting ice"],
            "audios": ["climate change speech recordings"],
            "videos": ["arctic wildlife documentary"]
        }
    },
    {
        "activity": "I watched videos about different types of cats",
        "queries": {
            "documents": ["cat breed characteristics"],
            "images": ["cute cat pictures", "different cat breeds"],
            "audios": ["cat purring sounds"],
            "videos": ["top 10 cat videos"]
        }
    },
    {
        "activity": "I was looking at cooking tutorials",
        "queries": {
            "documents": ["pasta recipes", "how to make fried rice guide"],
            "images": ["delicious pasta dishes"],
            "audios": ["cooking sounds"],
            "videos": ["fried rice tutorial"]
        }
    }
]

examples = format_examples(examples_raw)

# --- Prompt template ---
example_prompt = PromptTemplate(
    input_variables=["activity", "queries"],
    template="User activity: {activity}\nOutput: {queries}\n"
)

search_query_prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    prefix=(
        "You are an assistant that generates realistic and helpful human search queries "
        "based on what a user says they were doing.\n"
        "Do NOT just repeat the activity.\n"
        "Organize the queries into 4 types: documents, images, audios, and videos.\n"
        "Return a Python dictionary where each key ('documents', 'images', 'audios', 'videos') "
        "maps to a list of relevant search queries.\n"
        "Only output the Python dictionary. No extra explanation. DO not add markdown syntax around it, just return plain text.\n\n"
    ),
    suffix="User activity: {activity}\nOutput:",
    input_variables=["activity"]
)

# --- LLM model ---
load_dotenv()
llm = ChatOpenAI(model_name="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))

search_query_chain = search_query_prompt | llm

# --- Final function ---
def generate_search_queries(activity: str) -> dict:
    """Generate a dictionary of search queries from a user activity description."""
    response = search_query_chain.invoke({"activity": activity})
    try:
        queries = ast.literal_eval(response.content)
        if isinstance(queries, dict):
            return queries
        else:
            raise ValueError("Model output is not a dictionary.")
    except Exception as e:
        raise ValueError(f"Failed to parse model output: {e}")

# --- Example usage ---
if __name__ == "__main__":
    activity = "I want to recreate my activity where I read cat-related articles and watched funny cat videos at April 12, 2024"
    queries = generate_search_queries(activity)
    print(queries)
