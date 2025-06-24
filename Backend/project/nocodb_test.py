import requests

NOCO_URL = "https://answermagic.5cn.co.in/api/v1/db/data/noco"
PROJECT_ID = "pq66hsc5sj06r93"
TABLE_ID = "m71ldqche4y4kq9"  # conversation_logs
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InN1bmlsLmt1bWFyQDVjbmV0d29yay5jb20iLCJpZCI6InVzMW9hYnV4bjZjYjN3NjAiLCJyb2xlcyI6eyJvcmctbGV2ZWwtY3JlYXRvciI6dHJ1ZX0sInRva2VuX3ZlcnNpb24iOiJhNzVhYTBiMGU4YWEwYzA2NjdhZjA1ODUzZTRlNWE0N2I2MWY5NzNiMmIyYTYwNjJkNGY3ZTIyY2Q4ZjNkZDEwOGM5M2RjMjIyYzdjZTQ4MCIsImlhdCI6MTc0OTk3MDkxNCwiZXhwIjoxNzUwMDA2OTE0fQ.OriqtU-oq8ldT21GYcjRgC8sBVhEdJsWNysCw23CexM"

HEADERS = {
    "xc-auth": AUTH_TOKEN,
    "Content-Type": "application/json"
}

def test_nocodb():
    url = "https://answermagic.5cn.co.in/api/v1/db/data/noco/pq66hsc5sj06r93/m71ldqche4y4kq9/views/vwdme50jau0vmfuq?offset=0&limit=1"
    print(f"Testing NoCoDB API: {url}")
    try:
        response = requests.get(url, headers=HEADERS)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 200:
            print("✅ NoCoDB API is accessible and token is valid.")
        elif response.status_code == 403:
            print("❌ 403 Forbidden: Check your token and permissions.")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")

if __name__ == "__main__":
    test_nocodb()