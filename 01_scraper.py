
import requests
from datetime import datetime
import os
from typing import List, Dict, Tuple
import json
from bs4 import BeautifulSoup
import re



class CanvasToTodoistSync:
    def __init__(self, canvas_base_url: str, canvas_api_key: str):
        self.canvas_base_url = canvas_base_url
        self.canvas_api_key = canvas_api_key

    def get_canvas_headers(self) -> Dict:
        return {
            "Authorization": f"Bearer {self.canvas_api_key}"
        }

    def do_api_request(self, url: str, params: Dict) -> Dict:
        """Do generic request"""
        response = requests.get(
            url,
            headers=self.get_canvas_headers(),
            params=params
        )
        response.raise_for_status()

        return response.json()

    def get_active_courses(self) -> List[Dict]:
        """Get favorited active courses from Canvas"""
        response = requests.get(
            f"{self.canvas_base_url}/courses",
            headers=self.get_canvas_headers(),
            params={
                "enrollment_state": "active",
                "include[]": "favorites",
                "favorites": True,
                "per_page": 30

            }
        )
        response.raise_for_status()

        # Filter to only include favorited courses
        courses = response.json()

        return [course for course in courses if course.get('is_favorite', False)]
    
    def get_course_modules(self, course_id: int) -> List[Dict]:
        """Get all modules for a specific course"""
        modules = []

        # Get first page of modules
        url = f"{self.canvas_base_url}/courses/{course_id}/modules"
        params = {
            "include[]": "items",
        }
        response = requests.get(
            url,
            headers=self.get_canvas_headers(),
            params=params
        )
        response.raise_for_status()

        modules = response.json()
        return modules
    
    def get_course_pages(self, course_id: int) -> List[Dict]:
        url = f"{self.canvas_base_url}/courses/{course_id}/pages"
        params = {
            "include[]": "body"
        }

        return self.do_api_request(url, params)
    
    def get_course_page_details(self, course_id: int, page_id: int) -> List[Dict]:
        url = f"{self.canvas_base_url}/courses/{course_id}/pages/{page_id}"
        params = {
            # "include[]": "body"
        }

        return self.do_api_request(url, params)
    
    def get_quiz_submission(self, course_id: int, quiz_id: int) -> List[Dict]:
        url = f"{self.canvas_base_url}/courses/{course_id}/quizzes/{quiz_id}/submission"
        params = {
            "include[]": "quiz",
        }
        return self.do_api_request(url, params)
    
    def get_quiz_submission_details(self, course_id: int, quiz_id: int, submission_id: int) -> List[Dict]:
        url = f"{self.canvas_base_url}/courses/{course_id}/quizzes/{quiz_id}/submissions/{submission_id}"
        params = {
            # "include[]": "submission",
            # "include[]": "quiz",
            # "include[]": "user",
        }
        return self.do_api_request(url, params)
    
    def get_quiz_questions(self, course_id: int, quiz_id: int, submission_id: int) -> List[Dict]:
        # url = f"{self.canvas_base_url}/courses/{course_id}/quizzes/{quiz_id}/questions"
        # url = f"{self.canvas_base_url}/quiz_submissions/{quiz_id}/questions"
        url = f"{self.canvas_base_url}/courses/{course_id}/quizzes/{quiz_id}/questions"
        params = {
            # "quiz_submission_id": submission_id,
            # "include[]": "questions",
        }
        return self.do_api_request(url, params)

    def get_course_assignments(self, course_id: int) -> List[Dict]:
        """Get all assignments for a specific course"""
        assignments = []

        # Get first page of assignments
        url = f"{self.canvas_base_url}/courses/{course_id}/assignments"
        next_url, curr_url, response = self.get_page_assignments(url)

        # Add assignments to list
        assignments.extend(response)
        print(f"Found {len(assignments)} assignments")

        while(next_url and next_url != curr_url):
            next_url, curr_url, response = self.get_page_assignments(next_url)
            assignments.extend(response)
            print(f"Found {len(assignments)} assignments")

        return assignments

    def get_page_assignments(self, url: str) -> Tuple[str, str, List[Dict]]:
        """Get all assignments for a specific course"""
        params = {
            # "bucket": "upcoming",
            "include[]": "submission",
            "per_page": 30,
        }
        response = requests.get(
            url,
            headers=self.get_canvas_headers(),
            params=params
        )
        response.raise_for_status()

        # Get next page URL
        next_url = response.links['next']['url'] if 'next' in response.links else None
        curr_url = response.links['current']['url'] if 'current' in response.links else None

        return (next_url, curr_url, response.json())

canvas_domain = "umsystem.instructure.com"
canvas_base_url = f"https://{canvas_domain}/api/v1"
canvas_token = "16765~K67EK3Pu89RKhxhf7xGZH9BaJNEc2rmkrYHfQvPwzTRx6Lax4hzMH4wZDNuGPMV3"

def main():
    # Load the JSON file
    with open('C#_.NET_modules.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    quiz_urls = []

    for module in data:
        for item in module.get('items', []):
            if item.get('type') == "Quiz":
                quiz_urls.append(item['html_url'])

    print("\n".join(quiz_urls))

def local_sync():
    course_name = "C#/.NET"

    # Load the JSON file
    with open('C#_.NET_items.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Print the loaded data
    print(f"Loaded {len(data)} modules")

    all_bodies = ""

    for item in data:
        body_html = item.get('body', "")
        # Convert HTML to plain text
        plain_text = BeautifulSoup(body_html, "html.parser").get_text()
        # Remove extra spaces and newlines
        plain_text = re.sub(r'\n\n\n+', ' ', plain_text).strip()
        all_bodies += plain_text
        all_bodies += "\n"

        item['body'] = plain_text

    # Save the text to a file
    sanitized_course_name = course_name.replace(" ", "_").replace("/", "_")
    file_name = f"{sanitized_course_name}_bodies.txt"
    with open(file_name, "w", encoding="utf-8") as txt_file:
        txt_file.write(all_bodies)
    print(f"Bodies saved to {file_name}")

    # Save the modified data to a new JSON file
    file_name = f"{sanitized_course_name}_sanitized_items.json"
    with open(file_name, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Modified data saved to {file_name}")




def online_sync():
    canvas_sync = CanvasToTodoistSync(canvas_base_url, canvas_token)

    # Get active courses
    courses = canvas_sync.get_active_courses()
    print(f"Found {len(courses)} active courses")

    # Get modules for each course
    for course in courses:
        course_id = course['id']
        course_name = course['name']

        if not course_name == "C#/.NET":
            continue

        # Get all modules for course
        print(f"Getting modules for {course_name} ({course_id})")
        modules = canvas_sync.get_course_modules(course_id)
        print(f"Found {len(modules)} modules for {course_name}")
        
        # Save modules to a JSON file named after the course_name
        sanitized_course_name = course_name.replace(" ", "_").replace("/", "_")
        file_name = f"{sanitized_course_name}_modules.json"
        with open(file_name, "w", encoding="utf-8") as json_file:
            json.dump(modules, json_file, indent=4)
        print(f"Modules saved to {file_name}")

        all_items = []
        all_quiz_urls = []
        all_bodies = ""

        for module in modules:
            items = module.get('items', [])
            print(f"Found {len(items)} items in module {module['name']}")
            for item in items:
                item_type = item.get('type')
                item_id = item.get('page_url')
                print(f"Item type: {item_type}, Item ID: {item_id}")
                if item_type == "Quiz":
                    all_quiz_urls.append(item.get('html_url'))
                    pass
                elif item_type == "Assignment":
                    # assignment = canvas_sync.get_course_assignments(course_id)
                    # all_items.append(assignment)
                    pass
                elif item_type == "Page":
                    page = canvas_sync.get_course_page_details(course_id, item_id)
                    all_items.append(page)
                    all_bodies += page.get('body')
                    all_bodies += "\n\n"

        # Save items to a JSON file named after the course_name
        sanitized_course_name = course_name.replace(" ", "_").replace("/", "_")
        file_name = f"{sanitized_course_name}_items.json"
        with open(file_name, "w", encoding="utf-8") as json_file:
            json.dump(all_items, json_file, indent=4)
        print(f"Items saved to {file_name}")


        # Save bodies to a text file named after the course_name
        sanitized_course_name = course_name.replace(" ", "_").replace("/", "_")
        file_name = f"{sanitized_course_name}_bodies.txt"
        with open(file_name, "w", encoding="utf-8") as txt_file:
            txt_file.write(all_bodies)
        print(f"Bodies saved to {file_name}")

        # Save quiz URLs to a text file named after the course_name
        sanitized_course_name = course_name.replace(" ", "_").replace("/", "_")
        file_name = f"{sanitized_course_name}_quiz_urls.txt"
        with open(file_name, "w", encoding="utf-8") as txt_file:
            for url in all_quiz_urls:
                txt_file.write(url + "\n")
        print(f"Quiz URLs saved to {file_name}")
                


        # print(f"Getting pages for {course_name} ({course_id})")
        # pages = canvas_sync.get_course_pages(course_id)
        # print(f"Found {len(pages)} pages for {course_name}")
        
        # # Save pages to a JSON file named after the course_name
        # sanitized_course_name = course_name.replace(" ", "_").replace("/", "_")
        # file_name = f"{sanitized_course_name}_pages.json"
        # with open(file_name, "w", encoding="utf-8") as json_file:
        #     json.dump(pages, json_file, indent=4)
        # print(f"Pages saved to {file_name}")

if __name__ == "__main__":
    main()