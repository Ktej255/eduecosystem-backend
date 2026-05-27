import re

with open("app/api/api_v1/endpoints/sso.py", "r") as f:
    content = f.read()

content = re.sub(
    r'\s+expires=int\(access_token_expires\.total_seconds\(\)\),',
    '',
    content
)

with open("app/api/api_v1/endpoints/sso.py", "w") as f:
    f.write(content)
