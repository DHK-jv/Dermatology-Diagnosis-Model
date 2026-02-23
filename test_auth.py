import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        # Get token
        login_resp = await client.post("http://localhost/api/v1/auth/login", data={"username": "testuser", "password": "password123"})
        if login_resp.status_code != 200:
            print("Login failed:", login_resp.json())
            return
        
        token = login_resp.json()["access_token"]
        print("Got token")
        
        # Mock file upload to predict
        files = {'file': ('test.jpg', b'fake image content', 'image/jpeg')}
        headers = {"Authorization": f"Bearer {token}"}
        
        resp = await client.post("http://localhost/api/v1/predict", files=files, headers=headers)
        print("Status:", resp.status_code)
        
if __name__ == "__main__":
    asyncio.run(test())
