# AITXHackathon2025
Agentic AI for healthcare provider matching

## Django setup instructions
1. `cd` into `web_backend`
2. (First time setup only) Create a virtual environment: `python -m venv venv`
3. (First time setup only) Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Ensure you're in the `web_backend` root directory and run the local server: `uvicorn medmatch.asgi:application --reload`

## To log in to Django Admin
1. Go to `http://127.0.0.1:8000/admin`
2. Use the username and password provided to you

