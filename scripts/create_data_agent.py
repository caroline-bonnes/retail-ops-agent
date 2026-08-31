import google.auth
import google.auth.transport.requests
import requests


def create_data_agent():
    # 1. Get Application Default Credentials
    credentials, project_id = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    # Request/Refresh the authentication token
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)

    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }

    # 2. Define resources and IDs
    location = "global"
    agent_id = "retail-ops-bq-agent"

    # We construct the URL for POST request:
    # POST https://geminidataanalytics.googleapis.com/v1beta/projects/{project}/locations/{location}/dataAgents?dataAgentId={agent_id}
    url = f"https://geminidataanalytics.googleapis.com/v1beta/projects/{project_id}/locations/{location}/dataAgents"
    params = {"dataAgentId": agent_id}

    # 3. Build payload
    payload = {
        "displayName": "Retail Ops Data Agent",
        "description": "Analyzes mock retail store operations, inventory, and sales data in BigQuery.",
        "dataAnalyticsAgent": {
            "publishedContext": {
                "datasourceReferences": {
                    "bq": {
                        "tableReferences": [
                            {
                                "projectId": project_id,
                                "datasetId": "retail_ops",
                                "tableId": "stores",
                            },
                            {
                                "projectId": project_id,
                                "datasetId": "retail_ops",
                                "tableId": "inventory",
                            },
                            {
                                "projectId": project_id,
                                "datasetId": "retail_ops",
                                "tableId": "sales",
                            },
                            {
                                "projectId": project_id,
                                "datasetId": "retail_ops",
                                "tableId": "customer_satisfaction",
                            },
                        ]
                    }
                },
                "systemInstruction": "You are a retail operations data analyst. You answer natural language questions about store performance, manager details, inventory stock, transactions, sales amounts, and customer satisfaction ratings. Always retrieve data using the available tables. Keep answers factual and precise.",
            }
        },
    }

    # 4. Make request
    print(f"Creating Data Agent '{agent_id}' in project '{project_id}'...")
    response = requests.post(url, json=payload, headers=headers, params=params)

    if response.status_code in [200, 201]:
        print("Success! Data Agent created:")
        print(response.json())
    else:
        print(f"Failed to create Data Agent. Status: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    create_data_agent()
