import requests
import time
import json
from datetime import datetime, timedelta

CACHE = {}
API_URL = "https://api.5cnetwork.com/study/list"
STUDY_STATUSES = [
    "ACTIVATED", "RECEIVED", "CREATED", "UPLOADING", "IQC_REVIEW", "EQC_REVIEW",
    "IQC_COMPLETED", "IN_POOL", "FOLLOW_UP", "ASSIGNED", "OPENED", "REPORTED",
    "IQC_NON_REPORTABLE", "NON_REPORTABLE", "COMPLETED"
]

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer <YOUR_API_TOKEN>"  # Replace with your actual token
}

def get_time_range():
    now = datetime.utcnow()
    start = (now - timedelta(days=30)).replace(hour=18, minute=30, second=0, microsecond=0)
    end = now
    return start.isoformat() + 'Z', end.isoformat() + 'Z'

def transform_case_data(studies):
    all_cases = []
    for i, study in enumerate(studies):
        try:
            statuses = study.get("statuses") or []

            details = study.get("details") or {}
            technician_details = study.get("technician_details") or {}
            radiologist = study.get("radiologist") or {}

            case = {
                "internal_study_fk": study.get("id"),
                "order_id": study.get("order_id"),
                "patient_id": study.get("patient_id"),
                "patient_name": study.get("patient_name"),
                "study_types": study.get("studies") or [],
                "current_status": study.get("status"),

                "activated_time": next((s.get("date_time") for s in statuses if s.get("status") == "ACTIVATED"), None),
                "assigned_time": next((s.get("date_time") for s in statuses if s.get("status") == "ASSIGNED"), None),
                "reported_time": next((s.get("date_time") for s in statuses if s.get("status") == "REPORTED"), None),
                "completed_time": next((s.get("date_time") for s in statuses if s.get("status") == "COMPLETED"), None),

                "is_assigned": any(s.get("status") == "ASSIGNED" and s.get("completed") for s in statuses),
                "is_reported": any(s.get("status") == "REPORTED" and s.get("completed") for s in statuses),
                "is_completed": any(s.get("status") == "COMPLETED" and s.get("completed") for s in statuses),

                "is_critical": details.get("critical", False),
                "case_type": details.get("case_type"),
                "is_pro_rad_insights": details.get("is_pro_rad_insights", False),
                "is_onco": details.get("is_onco", False),
                "is_urgent": details.get("is_urgent", False),
                "favourite_case_pool": details.get("favourite_case_type") == "FAVOURITE_CASE_POOL",

                "radiologist": radiologist.get("display_name"),
                "technician_name": technician_details.get("name"),
                "technician_contact": technician_details.get("contact_no"),
            }
            all_cases.append(case)
        except Exception as e:
            print(f"❌ Exception in transform_case_data on study index {i}: {e}")
            print(f"Study data: {study}")
            continue
    return all_cases



def fetch_case_data_l30d(client_id):
    current_time = time.time()
    
    if client_id in CACHE and current_time - CACHE[client_id]["timestamp"] < 600:
        print("✅ Cache hit")
        return CACHE[client_id]["data"]

    start_date, end_date = get_time_range()

    params = {
        "client_id": client_id,
        "limit": 100,
        "study_type": "study",
        "start_date": start_date,
        "end_date": end_date,
        "saas_only": "false",
        "send_client_rework": "true",
        "role_id": "1"
    }

    for status in STUDY_STATUSES:
        params.setdefault("study_statuses[]", []).append(status)

    try:
        response = requests.get(API_URL, headers=HEADERS, params=params)
        response.raise_for_status()

        # ✅ Ensure it's JSON
        try:
            data = response.json()
            print("✅ JSON parsed successfully")
            print("🔍 Keys:", list(data.keys()))
            print("📄 Partial JSON Preview:", json.dumps({k: data[k] for k in list(data.keys())[:3]}, indent=2))
        except Exception as json_err:
            print("❌ Failed to parse JSON:", json_err)
            raise json_err

        studies = data.get("studies", [])
        transformed_cases = transform_case_data(studies)

        final_data = {
            "total_active_count_from_30d": data.get("count", 0),
            "total_cases_count_by_status": data.get("statusCount", {}),
            "all_active_cases_lists_from_30d": transformed_cases
        }

        CACHE[client_id] = {
            "timestamp": current_time,
            "data": final_data
        }

        return final_data

    except Exception as e:
        print("❌ Exception during fetch_case_data_l30d:", str(e))
        return {
            "error": str(e),
            "total_active_count_from_30d": 0,
            "total_cases_count_by_status": {},
            "all_active_cases_lists_from_30d": []
        }


if __name__ == "__main__":
    client_fk = 3866
    res = fetch_case_data_l30d(client_fk)
    print(json.dumps(res, indent=2))
