import asyncio
import httpx
import os

async def test():
    # Giả lập token
    async with httpx.AsyncClient() as client:
        # Get token
        login_resp = await client.post("http://localhost:8000/api/v1/auth/login", data={"username": "testuser", "password": "password123"})
        if login_resp.status_code != 200:
            print("Login failed, please create testuser password123")
            return
            
        token = login_resp.json()["access_token"]
        
        # Test image 
        # Create a mock black image if test.jpg doesn't exist
        if not os.path.exists("test.jpg"):
            import numpy as np
            import cv2
            img = np.zeros((380, 380, 3), dtype=np.uint8)
            cv2.imwrite("test.jpg", img)

        with open("test.jpg", "rb") as f:
            files = {'file': ('test.jpg', f, 'image/jpeg')}
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.post("http://localhost:8000/api/v1/predict", files=files, headers=headers)
            print("Response:", resp.json())
        
if __name__ == "__main__":
    asyncio.run(test())
