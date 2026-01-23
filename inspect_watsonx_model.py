
import os
import json
try:
    from ibm_watsonx_ai import APIClient, Credentials
    
    api_key = os.environ.get("WATSONX_API_KEY")
    url = os.environ.get("WATSONX_URL")
    project_id = os.environ.get("WATSONX_PROJECT_ID")
    
    if not api_key or not url:
        print("Missing WATSONX_API_KEY or WATSONX_URL")
        exit(1)

    creds = Credentials(url=url, api_key=api_key)
    client = APIClient(credentials=creds, project_id=project_id)
    
    model_id = "ibm/granite-4-h-small"
    print(f"Fetching specs for {model_id}...")
    try:
        spec = client.foundation_models.get_model_specs(model_id)
        print(json.dumps(spec, indent=2))
    except Exception as e:
        print(f"Could not get spec for {model_id}: {e}")
        # Try listing all again to see if we missed something about the structure
        all_models = client.foundation_models.get_model_specs()
        for m in all_models.get('resources', []):
            if m.get('model_id') == model_id:
                print(json.dumps(m, indent=2))

except Exception as e:
    print(f"Error: {e}")
