from langchain.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from datetime import datetime
import os
import ast
from typing import List, Dict, Optional
import json

def escape_braces(s: str) -> str:
    """Escape curly braces to avoid format errors."""
    return s.replace("{", "{{").replace("}", "}}")

def format_examples(examples_raw):
    """Convert examples with list/dict into proper string for FewShotPromptTemplate."""
    formatted = []
    for ex in examples_raw:
        formatted.append({
            "activity": ex["activity"],
            "files": "\n".join(ex["files"]),  # list -> string with newlines
            "output": escape_braces(json.dumps(ex["output"], indent=2))  # list of dict -> pretty JSON string + escape
        })
    return formatted

# Few-shot examples
examples = [
    {
        "activity": "I was researching climate change and polar bears",
        "files": [
            "/tmp/climate_effects_report.pdf",
            "/tmp/random_dog_picture.jpg",
            "/tmp/polar_bear_melting_ice.png"
        ],
        "output": [
            {
                "local_path": "/tmp/climate_effects_report.pdf",
                "target_path": "/home/user/Documents/climate_effects_report.pdf",
                "access_time": "2025-04-15 10:15:23",
                "modified_time": "2025-04-15 10:20:31"
            },
            {
                "local_path": "/tmp/polar_bear_melting_ice.png",
                "target_path": "/home/user/Pictures/polar_bear_melting_ice.png",
                "access_time": "2025-04-15 10:25:10",
                "modified_time": "2025-04-15 10:27:05"
            }
        ]
    },
    {
        "activity": "I was watching funny cat videos",
        "files": [
            "/tmp/cat_funny_1.mp4",
            "/tmp/cat_breed_info.txt",
            "/tmp/unrelated_politics_article.pdf"
        ],
        "output": [
            {
                "local_path": "/tmp/cat_funny_1.mp4",
                "target_path": "/home/user/Videos/cat_funny_1.mp4",
                "access_time": "2025-04-12 14:05:10",
                "modified_time": "2025-04-12 14:07:50"
            }
        ]
    }
]

examples = format_examples(examples)

# Example format
example_prompt = PromptTemplate(
    input_variables=["activity", "files", "output"],
    template=(
        "User activity: {activity}\n"
        "Downloaded files:\n{files}\n"
        "Selected file operations:\n{output}\n"
    )
)

# Prefix instructions
prefix = (
    "You are an intelligent assistant helping to reconstruct user behavior inside a Linux system.\n"
    "We have a clean disk image and want to recreate traces of user activities.\n\n"
    "Given:\n"
    "1. A user activity description.\n"
    "2. A list of downloaded files.\n\n"
    "Select only relevant files.\n"
    "- Ignore unrelated files.\n"
    "- Generate realistic target paths (/home/user/...) based on file type.\n"
    "- Generate reasonable access_time and modified_time.\n"
    "- Assume user name is 'user'.\n\n"
    "Output: a Python list of dictionaries with local_path, target_path, access_time, and modified_time. DO not add markdown syntax around it, just return plain text.\n"
)

# Few-shot prompt template
select_and_plan_prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    prefix=prefix,
    suffix=(
        "User activity: {activity}\n"
        "Downloaded files:\n{files}\n"
        "Current system time: {current_time}\n"
        "Selected file operations:\n"
    ),
    input_variables=["activity", "files", "current_time"]
)

# Initialize LLM
load_dotenv()
llm = ChatOpenAI(model_name="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))

# Chain with new syntax
select_and_plan_chain = select_and_plan_prompt | llm

def select_files_for_activity(activity: str, files: List[str], current_time: Optional[str] = None) -> List[Dict]:
    """Select relevant files and generate realistic file operation traces."""
    if current_time is None:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    files_formatted = "\n".join(files)
    response = select_and_plan_chain.invoke({
        "activity": activity,
        "files": files_formatted,
        "current_time": current_time
    })
    try:
        output = ast.literal_eval(response.content)
        if isinstance(output, list):
            return output
        else:
            raise ValueError("Model output is not a list.")
    except Exception as e:
        raise ValueError(f"Failed to parse model output: {e}")

# Example usage
if __name__ == "__main__":
    activity = "I was researching domestic cats and watched funny cat videos"
    download_record = [
        "./to_upload/aspcapro_cat_behavior_guide.pdf",
        "./to_upload/cat_care_basics.docx",
        "./to_upload/evolution_of_domestic_cats.pdf",
        "./to_upload/funny_cat_memes.jpg",
        "./to_upload/history_of_cat_breeds.txt",
        "./to_upload/feral_cat_population_study.pdf"
    ]
    selected_files = select_files_for_activity(activity, download_record)
    print(selected_files)