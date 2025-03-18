import requests
import json

canvas_domain = "umsystem.instructure.com"
canvas_base_url = f"https://{canvas_domain}/api/v1"
canvas_token = "16765~K67EK3Pu89RKhxhf7xGZH9BaJNEc2rmkrYHfQvPwzTRx6Lax4hzMH4wZDNuGPMV3"

# Replace with actual values
ACCESS_TOKEN = canvas_token
COURSE_ID = "296958"
QUIZ_ID = "635015"
QUIZ_SUBMISSION_ID = "9615763"

BASE_URL = canvas_base_url

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def get_quiz_submission_with_answers(course_id, quiz_id, submission_id):
    """Fetch quiz submission details."""
    url = f"{BASE_URL}/courses/{course_id}/quizzes/{quiz_id}/submissions/{submission_id}"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching submission: {response.status_code}")
        print(response.text)
        return None

def get_quiz_submission_answers(course_id, submission_id):
    """Fetch answers for the quiz submission."""
    url = f"{BASE_URL}/courses/{course_id}/quiz_submissions/{submission_id}/questions"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching answers: {response.status_code}")
        print(response.text)
        return None

def get_quiz_statistics(course_id, quiz_id):
    """Fetch quiz statistics (aggregated data about the quiz)."""
    url = f"{BASE_URL}/courses/{course_id}/quizzes/{quiz_id}/statistics"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching quiz statistics: {response.status_code}")
        print(response.text)
        return None

def main():
    # Get quiz submission details (this won't include answers directly)
    print(f"Fetching quiz submission for quiz ID {QUIZ_ID}...")
    submission_data = get_quiz_submission_with_answers(COURSE_ID, QUIZ_ID, QUIZ_SUBMISSION_ID)
    
    if submission_data:
        print("Quiz Submission Data:")
        print(json.dumps(submission_data, indent=2))
    
    # Get answers for the quiz submission
    # print(f"\nFetching answers for quiz submission ID {QUIZ_SUBMISSION_ID}...")
    # answers_data = get_quiz_submission_answers(COURSE_ID, QUIZ_SUBMISSION_ID)
    
    # if answers_data:
    #     print("Quiz Submission Answers:")
    #     print(json.dumps(answers_data, indent=2))
    
    # Get quiz statistics
    print(f"\nFetching quiz statistics for quiz ID {QUIZ_ID}...")
    statistics_data = get_quiz_statistics(COURSE_ID, QUIZ_ID)
    
    if statistics_data:
        print("Quiz Statistics:")
        print(json.dumps(statistics_data, indent=2))

if __name__ == "__main__":
    main()