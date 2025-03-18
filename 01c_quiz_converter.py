import json
import os
from bs4 import BeautifulSoup

# Combine all json files from quiz_json directory
# into a single list of dictionaries
quiz_data = []
output_data = []
output_object = []

# Iterate through all files in the directory
for filename in os.listdir("./quiz_json"):
    if filename.endswith(".json"):  # Only process JSON files
        file_path = os.path.join("./quiz_json", filename)
        with open(file_path, "r") as f:
            data = json.load(f)
            quiz_data.extend(data)  # Assuming each file contains a list of dictionaries

for question in quiz_data:
    question_text = question.get("question", "")
    
    # Extract the question text
    soup = BeautifulSoup(question_text, "html.parser")
    question_text = soup.get_text()

    text = "Question: " + question_text + "\nAnswer Options:\n"

    for answer in question.get("answers", []):
        text += answer.get("content", "") + " "
        text += "(Correct)" if answer.get("correct", False) else "(Incorrect)"
        text += "\n"
    
    text += "---\n"

    output_data.append(text)
    output_object.append({
        "body": text
    })

# Write the output data to a text file
with open("all_quiz_output.txt", "w") as f:
    for line in output_data:
        f.write(line + "\n")

# Write the output data to a JSON file
with open("all_quiz_output.json", "w") as f:
    json.dump(output_object, f, indent=4)