import asyncio
import json
import os
import sys

# Add the parent directory to the path so we can import the api
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import aiohttp
from custom_components.velux_active.api import VeluxActiveApi
from custom_components.velux_active.const import DEFAULT_CLIENT_ID, DEFAULT_CLIENT_SECRET

async def main():
    print("=== Velux Active API Data Dumper ===")
    username = input("Email address: ")
    password = input("Password: ")
    
    print()
    print("Authenticating...")
    async with aiohttp.ClientSession() as session:
        api = VeluxActiveApi(
            session, 
            username, 
            password, 
            DEFAULT_CLIENT_ID, 
            DEFAULT_CLIENT_SECRET
        )
        
        try:
            await api.async_authenticate()
            print("Authentication successful!")
        except Exception as e:
            print(f"Authentication failed: {e}")
            return
            
        print()
        print("Fetching homesdata...")
        try:
            homesdata = await api.async_get_homes_data()
            with open("homesdata_dump.json", "w") as f:
                json.dump(homesdata, f, indent=2)
            print("Saved homesdata to homesdata_dump.json")
            
            # Print a quick summary of found modules to the console
            homes = homesdata.get("body", {}).get("homes", [])
            for home in homes:
                print()
                print(f"Home: {home.get('name', home.get('id'))}")
                print("-" * 40)
                
                # Check top-level modules
                print("Modules array:")
                for module in home.get("modules", []):
                    m_id = module.get("id")
                    m_name = module.get("name", "<NO NAME>")
                    m_type = module.get("type", "<NO TYPE>")
                    v_type = module.get("velux_type", "")
                    print(f"  - ID: {m_id} | Name: {m_name} | Type: {m_type} | Velux Type: {v_type}")
                
                # Check rooms
                print()
                print("Rooms array:")
                for room in home.get("rooms", []):
                    r_id = room.get("id")
                    r_name = room.get("name", "<NO NAME>")
                    print(f"  - Room: {r_name} (ID: {r_id})")
                    
        except Exception as e:
            print(f"Failed to fetch homesdata: {e}")
            
        print()
        print("Fetching homestatus for the first home...")
        try:
            if homes:
                home_id = homes[0].get("id")
                homestatus = await api.async_get_home_status(home_id)
                with open("homestatus_dump.json", "w") as f:
                    json.dump(homestatus, f, indent=2)
                print("Saved homestatus to homestatus_dump.json")
                
                print()
                print("Home Status Modules:")
                for module in homestatus.get("body", {}).get("home", {}).get("modules", []):
                    m_id = module.get("id")
                    m_type = module.get("type", "<NO TYPE>")
                    silent = module.get("silent", "N/A")
                    print(f"  - ID: {m_id} | Type: {m_type} | Silent: {silent}")
                
            else:
                print("No homes found to fetch status for.")
        except Exception as e:
            print(f"Failed to fetch homestatus: {e}")

if __name__ == "__main__":
    asyncio.run(main())
