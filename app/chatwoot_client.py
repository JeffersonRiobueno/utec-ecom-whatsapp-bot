import httpx

async def add_chatwoot_label(conversation_id: str, label: str):
    # Asegúrate de que la URL sea dinámica (o fija si así se requiere, pero el usuario pidió dinámica basada en ID)
    # URL template: http://192.168.18.32:3000/api/v1/accounts/1/conversations/{conversation_id}/labels
    url = f"http://192.168.18.32:3000/api/v1/accounts/1/conversations/{conversation_id}/labels"
    headers = {
        "api_access_token": "uP4dPFSh9wxyDfs6gSXw9huu",
        "Content-Type": "application/json"
    }
    data = {"labels": [label]}
    
    print(f"[DEBUG] Adding label '{label}' to conversation {conversation_id} at {url}")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, headers=headers, json=data)
            if resp.status_code >= 200 and resp.status_code < 300:
                print(f"[INFO] Label added successfully: {resp.status_code}")
            else:
                print(f"[WARN] Failed to add label. Status: {resp.status_code}, Body: {resp.text}")
    except Exception as e:
        print(f"[ERROR] Exception adding label to Chatwoot: {e}")
