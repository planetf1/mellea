
import os
import json
try:
    from ibm_watsonx_ai import APIClient, Credentials
    
    api_key = os.environ.get("WATSONX_API_KEY")
    project_id = os.environ.get("WATSONX_PROJECT_ID")
    url = os.environ.get("WATSONX_URL")
    
    if not api_key or not url:
        print("Missing WATSONX_API_KEY or WATSONX_URL")
        exit(1)

    creds = Credentials(url=url, api_key=api_key)
    client = APIClient(credentials=creds, project_id=project_id)
    
    print("Fetching available foundation models...")
    models = client.foundation_models.get_model_specs()
    
    print("\nGranite Models Found:")
    found = False
    for model in models.get('resources', []):
        model_id = model.get('model_id')
        if 'granite' in model_id.lower():
            print(f"- {model_id}")
            found = True
            
    if not found:
        print("No models containing 'granite' found.")

except ImportError:
    print("ibm_watsonx_ai not installed")
except Exception as e:
    print(f"Error: {e}")
