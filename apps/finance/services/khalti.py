import requests
import os
import json
from django.conf import settings

class KhaltiService:
    """
    Integration with Khalti E-Payment API (v2).
    Docs: https://docs.khalti.com/khalti-epayment/
    """
    
    BASE_URL_SANDBOX = "https://a.khalti.com/api/v2/epayment"
    BASE_URL_PROD = "https://khalti.com/api/v2/epayment" # verify prod url

    def __init__(self):
        self.is_prod = os.environ.get("KHALTI_ENV", "sandbox").lower() == "prod"
        self.base_url = self.BASE_URL_PROD if self.is_prod else self.BASE_URL_SANDBOX
        self.secret_key = os.environ.get("KHALTI_SECRET_KEY", "")
        
        if not self.secret_key:
            # warn or log
            pass

    def get_headers(self):
        return {
            "Authorization": f"Key {self.secret_key}",
            "Content-Type": "application/json",
        }

    def initiate_payment(self, payment_obj, return_url, website_url):
        """
        Initiate payment request.
        """
        url = f"{self.base_url}/initiate/"
        payload = {
            "return_url": return_url,
            "website_url": website_url,
            "amount": int(payment_obj.amount * 100), # Amount in paisa
            "purchase_order_id": str(payment_obj.id),
            "purchase_order_name": f"Invoice Payment {payment_obj.invoice.invoice_number if payment_obj.invoice else ''}",
            "customer_info": {
               "name": payment_obj.invoice.tenant.full_name if payment_obj.invoice and payment_obj.invoice.tenant else "Guest",
               "email": payment_obj.invoice.tenant.email if payment_obj.invoice and payment_obj.invoice.tenant else "guest@example.com",
               "phone": payment_obj.invoice.tenant.phone if payment_obj.invoice and payment_obj.invoice.tenant else "",
            }
        }
        
        try:
            response = requests.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            data = response.json()
            # Expected: { "pidx": "...", "payment_url": "...", "expires_at": "...", "expires_in": ... }
            return data
        except requests.exceptions.RequestException as e:
            # Generic error handling
            print(f"Khalti Initiate Error: {e}")
            if e.response:
                print(e.response.text)
            return None

    def verify_payment(self, pidx):
        """
        Verify payment using pidx.
        """
        url = f"{self.base_url}/lookup/"
        payload = {"pidx": pidx}
        
        try:
            response = requests.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            data = response.json()
            # Expected: { "pidx": "...", "status": "Completed", "transaction_id": "...", "total_amount": ..., ... }
            return data
        except requests.exceptions.RequestException as e:
            print(f"Khalti Verify Error: {e}")
            return None
