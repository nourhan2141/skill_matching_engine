import uvicorn

if __name__ == "__main__":
    # Run the application entry point located in app/main.py
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
