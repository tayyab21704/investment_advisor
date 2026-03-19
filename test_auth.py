import urllib.request
import json
url = 'http://127.0.0.1:8000/api/auth/register'
data = {'name':'Test User','email':'testpy1@example.com','password':'password123','behavioral_risk_score':5,'financial_risk_score':5,'actual_risk_capacity':5,'monthly_income':100000,'monthly_expenses':50000,'monthly_surplus':50000,'existing_debt':10000,'debt_to_income_ratio':0.1,'liquidity_required_pct':20.0,'max_single_asset_pct':15.0,'max_high_risk_allocation_pct':40.0,'investment_horizon_years':10}
req = urllib.request.Request(url, json.dumps(data).encode('utf-8'), {'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        print('Status:', response.status)
        print('Body:', response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code)
    print('Error Body:', e.read().decode('utf-8'))
except Exception as e:
    print('Error:', e)
