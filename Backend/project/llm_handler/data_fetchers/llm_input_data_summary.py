from .L30_case_data_fetcher import fetch_case_data_l30d

def llm_last_30d_case_summary(client_fk):
    try:
        summary_data = fetch_case_data_l30d(client_fk)

        if summary_data is None:
            print("❌ fetch_case_data_l30d returned None")
            return "No data for last 30 days"

        if "error" in summary_data:
            print("❌ Error from fetch_case_data_l30d:", summary_data["error"])
            return "No data for last 30 days"

        llm_input = f"""
        We have {summary_data['total_active_count_from_30d']} active cases in the last 30 days.
        Breakdown by status: {summary_data['total_cases_count_by_status']}.
        All Active cases: {summary_data['all_active_cases_lists_from_30d'][:3]}.
        """
        return llm_input

    except Exception as e:
        print("❌ Error fetching case summary:", str(e))
        return "Error fetching last 30d case summary"


if __name__ == "__main__":
    client_fk = 3866
    print(llm_last_30d_case_summary(client_fk))