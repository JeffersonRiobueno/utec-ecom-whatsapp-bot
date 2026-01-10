import httpx
import asyncio

async def test_webhook():
    url = "https://reporte-seo.jeffersonriobueno.com/webhook/chatwood-bot"
    
    # Payload 1: Sending "0" as conversation_id
    data_0 = {
        "user": "51900000000",
        "mensaje": "Test message with ID 0",
        "type": "incoming",
        "conversation_id": "0"
    }
    
    # Payload 2: Sending phone number as conversation_id
    data_phone = {
        "user": "51900000000",
        "mensaje": "Test message with phone ID",
        "type": "incoming",
        "conversation_id": "51900000000"
    }
    
    headers = {"Content-Type": "application/json"}
    
    print(f"--- Testing with conversation_id='0' ---")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=data_0, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

    print(f"\n--- Testing with conversation_id='51900000000' ---")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=data_phone, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_webhook())
