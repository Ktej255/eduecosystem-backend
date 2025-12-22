from fastapi import FastAPI, APIRouter

app = FastAPI()
router = APIRouter()

print("Including empty router...")
try:
    app.include_router(router, prefix="/test", tags=["test"])
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()
