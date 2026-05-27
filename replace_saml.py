import re

with open("app/api/api_v1/endpoints/sso.py", "r") as f:
    content = f.read()

# Replace SAML
# redirect_url = f"{settings.BASE_URL}/auth/callback?token={access_token}"
# return RedirectResponse(url=redirect_url, status_code=303)

replacement = """    redirect_url = f"{settings.BASE_URL}/auth/callback"
    response = RedirectResponse(url=redirect_url, status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=int(access_token_expires.total_seconds()),
        expires=int(access_token_expires.total_seconds()),
        samesite="lax",
        secure=os.getenv("ENVIRONMENT") == "production",
    )
    return response"""

content = re.sub(
    r'    # Redirect to frontend with token\n    # In production, use a secure cookie or a redirect with a short-lived code\n    redirect_url = f"\{settings.BASE_URL\}/auth/callback\?token=\{access_token\}"\n    return RedirectResponse\(url=redirect_url, status_code=303\)',
    '    # Redirect to frontend without token in URL\n' + replacement,
    content
)

# And similarly for OAuth:
content = re.sub(
    r'        # Redirect to frontend\n        redirect_url = f"\{settings.BASE_URL\}/auth/callback\?token=\{access_token\}"\n        return RedirectResponse\(url=redirect_url, status_code=303\)',
    '        # Redirect to frontend without token in URL\n    ' + replacement.replace('    ', '        ').replace('        redirect_url', 'redirect_url'),
    content
)


with open("app/api/api_v1/endpoints/sso.py", "w") as f:
    f.write(content)
