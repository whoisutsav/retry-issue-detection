#!/usr/bin/python3

import csv
import shutil
import os
import random
import string

def copy_files_from_csv(csv_file, column_index, destination_directory):
    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header row if present

        for row in csv_reader:
            try:
                relative_path = row[column_index].strip()
                new_file_name=relative_path.replace("/","_")
                if relative_path:  # Check if the path is not empty
                    file_path=os.path.join("/Users/utsavsethi/workspace/retry-issue-detection/llm/repos/elasticsearch_7556157", relative_path)
                    new_file_path = os.path.join(destination_directory, new_file_name)

                    shutil.copy(file_path, new_file_path)
                    print(f"File copied: {file_path} -> {new_file_path}")
                else:
                    print("Skipping empty file path.")
            except Exception as e:
                print(f"Error copying file: {e}")

# Example usage:
csv_file_path = 'testset4_elastic.csv'  # Replace with the path to your CSV file
column_index_to_copy = 0  # Replace with the index of the column containing file paths (0-based index)
destination_directory = 'testset4_elastic'  # Replace with the path to your destination directory

# Create the destination directory if it doesn't exist
os.makedirs(destination_directory, exist_ok=True)

# Run the script
copy_files_from_csv(csv_file_path, column_index_to_copy, destination_directory)
