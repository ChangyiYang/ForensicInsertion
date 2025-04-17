from langchain.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import ast

# Few-shot examples
examples = [
    {
        "activity": "I was reading about climate change and polar bears",
        "queries": '["effects of climate change", "polar bear habitat loss", "how melting ice affects arctic animals"]'
    },
    {
        "activity": "I watched videos about different types of cats",
        "queries": '["funny cat videos", "maine coon vs ragdoll", "top 10 cat breeds", "cat behavior explained"]'
    },
    {
        "activity": "I was looking at cooking tutorials",
        "queries": '["easy pasta recipes", "how to make fried rice", "best kitchen tools 2024"]'
    }
]

# Format for examples
example_prompt = PromptTemplate(
    input_variables=["activity", "queries"],
    template="User activity: {activity}\nOutput: {queries}\n"
)

# Few-shot prompt
search_query_prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    prefix=(
        "You are an assistant that generates realistic and helpful human search queries "
        "based on what a user says they were doing.\n"
        "Do NOT just repeat the activity.\n"
        "Generate natural, creative, and diverse search engine queries.\n"
        "Only return a Python list of strings. No extra explanation.\n\n"
    ),
    suffix="User activity: {activity}\nOutput:",
    input_variables=["activity"]
)

# Initialize LLM
load_dotenv()
llm = ChatOpenAI(model_name="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))

# New chain syntax (no LLMChain!)
search_query_chain = search_query_prompt | llm

def generate_search_queries(activity: str) -> list:
    """Generate a list of search queries from a user activity description."""
    response = search_query_chain.invoke({"activity": activity})
    try:
        queries = ast.literal_eval(response.content)
        if isinstance(queries, list):
            return queries
        else:
            raise ValueError("Model output is not a list.")
    except Exception as e:
        raise ValueError(f"Failed to parse model output: {e}")

# Example usage
if __name__ == "__main__":
    activity = "I want to recreate my activity where I read cat-related articles and watched funny cat videos at April 12, 2024"
    queries = generate_search_queries(activity)
    print(queries)
