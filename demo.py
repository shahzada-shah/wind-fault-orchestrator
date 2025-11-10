"""
Demo script to showcase the Wind Fault Orchestrator API.

Run this after starting the server to see the API in action.
"""

import asyncio
from datetime import datetime

import httpx

BASE_URL = "http://localhost:8000/api/v1"


async def demo():
    """Run a complete demo of the API."""
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("Wind Fault Orchestrator API Demo")
        print("=" * 60)
        print()

        # Step 1: Register turbines
        print("1. Registering wind turbines...")
        turbines = [
            {
                "turbine_id": "WT-001",
                "name": "Wind Turbine 1",
                "location": "North Field",
                "model": "Vestas V90",
                "capacity_kw": 2000,
                "installation_date": "2020-01-15T00:00:00",
                "is_active": True,
            },
            {
                "turbine_id": "WT-002",
                "name": "Wind Turbine 2",
                "location": "South Field",
                "model": "Siemens SWT-3.6",
                "capacity_kw": 3600,
                "installation_date": "2021-06-20T00:00:00",
                "is_active": True,
            },
            {
                "turbine_id": "WT-003",
                "name": "Wind Turbine 3",
                "location": "East Field",
                "model": "GE 2.5-120",
                "capacity_kw": 2500,
                "installation_date": "2019-11-10T00:00:00",
                "is_active": True,
            },
        ]

        for turbine in turbines:
            response = await client.post(f"{BASE_URL}/turbines", json=turbine)
            if response.status_code == 201:
                print(f"   ✓ Registered: {turbine['turbine_id']} - {turbine['name']}")
            elif response.status_code == 400:
                print(f"   ⚠ Already exists: {turbine['turbine_id']}")
            else:
                print(f"   ✗ Error: {response.status_code}")

        print()

        # Step 2: Ingest alarms
        print("2. Ingesting turbine alarms...")
        alarms = [
            {
                "turbine_id": "WT-001",
                "alarm_code": "GEARBOX_TEMP_HIGH",
                "alarm_description": "Gearbox temperature exceeds 85°C",
                "severity": "high",
                "occurred_at": datetime.utcnow().isoformat(),
            },
            {
                "turbine_id": "WT-002",
                "alarm_code": "GENERATOR_VIBRATION",
                "alarm_description": "Abnormal vibration detected in generator",
                "severity": "high",
                "occurred_at": datetime.utcnow().isoformat(),
            },
            {
                "turbine_id": "WT-003",
                "alarm_code": "YAW_ERROR",
                "alarm_description": "Yaw system misalignment detected",
                "severity": "medium",
                "occurred_at": datetime.utcnow().isoformat(),
            },
            {
                "turbine_id": "WT-001",
                "alarm_code": "GRID_DISCONNECT",
                "alarm_description": "Lost connection to power grid",
                "severity": "critical",
                "occurred_at": datetime.utcnow().isoformat(),
            },
        ]

        alarm_ids = []
        for alarm in alarms:
            response = await client.post(f"{BASE_URL}/alarms", json=alarm)
            if response.status_code == 201:
                data = response.json()
                alarm_ids.append(data["id"])
                print(
                    f"   ✓ Alarm ingested: {alarm['turbine_id']} - {alarm['alarm_code']}"
                )
                print(
                    f"     Recommendation auto-generated (ID: {data['id']})"
                )
            else:
                print(f"   ✗ Error: {response.status_code}")

        print()

        # Step 3: List all turbines
        print("3. Listing all turbines...")
        response = await client.get(f"{BASE_URL}/turbines")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total turbines: {data['total']}")
            for turbine in data["turbines"]:
                status = "🟢 Active" if turbine["is_active"] else "🔴 Inactive"
                print(
                    f"   - {turbine['turbine_id']}: {turbine['name']} ({turbine['capacity_kw']} kW) {status}"
                )

        print()

        # Step 4: List active alarms
        print("4. Listing active alarms...")
        response = await client.get(f"{BASE_URL}/alarms?status=active")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total active alarms: {data['total']}")
            for alarm in data["alarms"]:
                severity_icons = {
                    "low": "🟢",
                    "medium": "🟡",
                    "high": "🟠",
                    "critical": "🔴",
                }
                icon = severity_icons.get(alarm["severity"], "⚪")
                print(
                    f"   {icon} Alarm #{alarm['id']}: {alarm['alarm_code']} - {alarm['severity'].upper()}"
                )
                print(f"      {alarm['alarm_description']}")

        print()

        # Step 5: Get recommendations
        print("5. Listing recommendations (sorted by priority)...")
        response = await client.get(f"{BASE_URL}/recommendations")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total recommendations: {data['total']}")
            for rec in data["recommendations"]:
                priority_icons = {
                    "low": "🟢",
                    "medium": "🟡",
                    "high": "🟠",
                    "urgent": "🔴",
                }
                icon = priority_icons.get(rec["priority"], "⚪")
                auto = "🤖 Auto" if rec["is_automated"] else "👤 Manual"
                print(f"   {icon} {rec['priority'].upper()}: {rec['title']} {auto}")
                print(f"      {rec['description']}")
                if rec["estimated_downtime_hours"]:
                    print(
                        f"      ⏱ Estimated downtime: {rec['estimated_downtime_hours']} hours"
                    )

        print()

        # Step 6: Acknowledge an alarm
        if alarm_ids:
            print(f"6. Acknowledging alarm #{alarm_ids[0]}...")
            response = await client.post(
                f"{BASE_URL}/alarms/{alarm_ids[0]}/acknowledge"
            )
            if response.status_code == 200:
                print(f"   ✓ Alarm #{alarm_ids[0]} acknowledged")

        print()

        # Step 7: Get recommendations for specific alarm
        if alarm_ids:
            print(f"7. Getting recommendations for alarm #{alarm_ids[0]}...")
            response = await client.get(f"{BASE_URL}/recommendations/{alarm_ids[0]}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Found {data['total']} recommendation(s)")
                for rec in data["recommendations"]:
                    print(f"   - {rec['title']}")
                    print(f"     Priority: {rec['priority']}")

        print()

        # Step 8: Health check
        print("8. Checking API health...")
        response = await client.get("http://localhost:8000/api/v1/health")
        if response.status_code == 200:
            data = response.json()
            status_icon = "✓" if data["status"] == "healthy" else "✗"
            print(f"   {status_icon} API Status: {data['status']}")
            print(f"   Database: {data['database']}")
            print(f"   Version: {data['version']}")

        print()
        print("=" * 60)
        print("Demo completed! Visit http://localhost:8000/docs for more.")
        print("=" * 60)


if __name__ == "__main__":
    print()
    print("Make sure the API server is running:")
    print("  uvicorn app.main:app --reload")
    print()
    print("Starting demo in 2 seconds...")
    import time

    time.sleep(2)
    print()

    try:
        asyncio.run(demo())
    except httpx.ConnectError:
        print("❌ Error: Could not connect to API server.")
        print("Please make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

