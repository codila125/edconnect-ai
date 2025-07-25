import requests

response = requests.get('http://localhost:11434/api/tags', timeout=10)
models = response.json()['models']
print('Available models:')
for m in models:
    print(f"- {m['name']} ({m['details']['parameter_size']})")
