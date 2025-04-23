import sys
from datetime import datetime
import os
import getpass
import ast

from LLM.search_and_query_chain import generate_search_queries
from insertion.downloadfiles import download_file
from LLM.select_and_plan_chain import select_files_for_activity
from insertion.insertion import insert_files_into_dd

import shutil
import os

def clear_to_upload_folder():
    folder_path = "./to_upload"
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path)

def main():
    # Check if verbose mode is enabled
    verbose = "-v" in sys.argv

    clear_to_upload_folder()

    # Step 1: Ask for user activity
    activity = input("Enter the user activity description: ").strip()

    if not activity:
        print("Error: Activity cannot be empty.")
        return

    # Step 2: Generate search queries
    print("Generating search queries...")
    search_queries = generate_search_queries(activity)
    
    if verbose:
        print("Generated search queries:")
        for q, words in search_queries.items():
            print(f"  - {q} : {', '.join(words)}")

    # Step 3: Download files for each query
    print("Downloading files...")
    download_record = download_file(search_queries)

    if not download_record:
        print("No files downloaded. Exiting.")
        return

    if verbose:
        print("Downloaded files:")
        for f in download_record:
            print(f"  - {f}")

    # Step 4: Select relevant files and generate file operation plans
    print("Selecting files and planning file operations...")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_operations = select_files_for_activity(activity, download_record, current_time=current_time)

    if not file_operations:
        print("No relevant files selected. Exiting.")
        return

    if verbose:
        print("Planned file operations:")
        for op in file_operations:
            print(f"  - Local: {op['local_path']} -> Target: {op['target_path']}")
            print(f"    Access time: {op['access_time']}, Modified time: {op['modified_time']}")

    target_paths_file = "./target_paths.txt"
    with open(target_paths_file, "w") as f:
        for op in file_operations:
            f.write(op["target_path"] + "\n")
    if verbose:
        print(f"All target paths have been saved to {target_paths_file}")


    # Step 5: Insert files into the disk image
    max_retries = 3
    for attempt in range(max_retries):
        image_file = input("Enter the path to the Linux .dd image: ").strip()
        
        if os.path.exists(image_file):
            break  
        else:
            print(f"Error: {image_file} does not exist.")
            if attempt < max_retries - 1:
                print("Please try again.")
            else:
                print("Max retries exceeded. Exiting.")
                return


    insert_files_into_dd(image_file, file_operations)

    print("All operations completed successfully.")

if __name__ == "__main__":
    main()
