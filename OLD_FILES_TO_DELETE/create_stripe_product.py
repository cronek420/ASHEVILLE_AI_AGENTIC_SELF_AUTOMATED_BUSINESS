import os
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_payment_link():
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
    
    if not stripe.api_key:
        print("[ERROR] STRIPE_SECRET_KEY not found in .env file.")
        print("Please add your Stripe Secret Key to the .env file like this:")
        print("STRIPE_SECRET_KEY=sk_test_12345...")
        return

    print("Authenticating with Stripe...")
    
    try:
        tiers = [
            {"name": "Asheville AI Audit - $149 Full Service", "amount": 14900, "desc": "Full upfront payment for $149 service."},
            {"name": "Asheville AI Audit - $75 Deposit", "amount": 7500, "desc": "Upfront deposit for $149 service."},
            {"name": "Asheville AI Audit - $74 Balance", "amount": 7400, "desc": "Final balance for $149 service."},
            
            {"name": "Asheville AI Audit - $99 Full Service", "amount": 9900, "desc": "Full upfront payment for $99 service."},
            {"name": "Asheville AI Audit - $50 Deposit", "amount": 5000, "desc": "Upfront deposit for $99 service."},
            {"name": "Asheville AI Audit - $49 Balance", "amount": 4900, "desc": "Final balance for $99 service."},
            
            {"name": "Asheville AI Audit - $75 Full Service", "amount": 7500, "desc": "Full upfront payment for $75 service."},
            {"name": "Asheville AI Audit - $40 Deposit", "amount": 4000, "desc": "Upfront deposit for $75 service."},
            {"name": "Asheville AI Audit - $35 Balance", "amount": 3500, "desc": "Final balance for $75 service."}
        ]

        print("\n=======================================================")
        for d in tiers:
            print(f"Creating product '{d['name']}' for ${d['amount']/100:.2f}...")
            product = stripe.Product.create(
                name=d['name'],
                description=d['desc']
            )

            price = stripe.Price.create(
                unit_amount=d['amount'],
                currency="usd",
                product=product.id,
            )

            payment_link = stripe.PaymentLink.create(
                line_items=[{"price": price.id, "quantity": 1}],
                metadata={"campaign": "G3_Outreach"}
            )
            
            print(f"SUCCESS! Link for ${d['amount']/100:.2f} Payment: {payment_link.url}")
            print("-------------------------------------------------------")

        print("Copy these links and provide them back to the agent!")

    except stripe.error.AuthenticationError:
        print("[ERROR] Invalid Stripe API Key provided. Please check your .env file.")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    create_payment_link()
