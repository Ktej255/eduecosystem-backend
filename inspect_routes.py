from main import app

for route in app.routes:
    # Handle different route types (APIRoute, Mount, etc.)
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', None)
        print(f"{methods} {route.path}")
    else:
        print(f"Unknown route type: {route}")
