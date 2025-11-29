import asyncio
from pprint import pprint

from agents.token_trust_orchestrator import TokenTrustOrchestrator


async def run_demo():
    orchestrator = TokenTrustOrchestrator()

    # Three test transactions
    tx_low = {
        "token": "tok_low_0001",
        "merchant_id": "merch_001",
        "amount": 10.0,
        "token_age_minutes": 1000,
        "device_trust_score": 0.9,
        "usual_location": "Mumbai,IN",
        "current_location": "Mumbai,IN",
        "user_avg_amount": 12.0,
        "new_device": False,
        "vpn_detected": False,
        "unusual_time": False,
        "rushed_transaction": False
    }

    tx_medium = {
        "token": "tok_med_0002",
        "merchant_id": "merch_002",
        "amount": 200.0,
        "token_age_minutes": 60,
        "device_trust_score": 0.6,
        "usual_location": "Delhi,IN",
        "current_location": "Delhi,IN",
        "user_avg_amount": 60.0,
        "new_device": True,
        "vpn_detected": False,
        "unusual_time": False,
        "rushed_transaction": False
    }

    tx_high = {
        "token": "tok_high_0003",
        "merchant_id": "merch_003",
        "amount": 1000.0,
        "token_age_minutes": 1,
        "device_trust_score": 0.2,
        "usual_location": "Bangalore,IN",
        "current_location": "Hyderabad,IN",
        "user_avg_amount": 20.0,
        "new_device": True,
        "vpn_detected": True,
        "unusual_time": True,
        "rushed_transaction": True
    }

    transactions = [
        ("low", tx_low),
        ("medium", tx_medium),
        ("high", tx_high)
    ]

    async def start_and_maybe_simulate(label, tx):
        # Start processing in background
        task = asyncio.create_task(orchestrator.process_transaction(tx))

        # Wait until orchestrator has created a session for this token
        session_id = None
        for _ in range(50):
            # Search active_sessions for matching token
            for sid, s in orchestrator.active_sessions.items():
                if s.get("transaction_data", {}).get("token") == tx["token"]:
                    session_id = sid
                    break
            if session_id:
                break
            await asyncio.sleep(0.05)

        # For medium label, simulate immediate merchant verification
        if label == "medium" and session_id:
            # Give a tiny moment for request_2fa to register
            await asyncio.sleep(0.1)
            # Simulate merchant responding YES
            await orchestrator.merchant_communicator.simulate_merchant_response(session_id, True)

        result = await task
        print(f"\n=== RESULT for {label} transaction ===")
        pprint(result)

    # Run transactions sequentially to keep output readable
    for label, tx in transactions:
        await start_and_maybe_simulate(label, tx)


if __name__ == "__main__":
    asyncio.run(run_demo())
