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


## To run the mobile app
1. `cd` into `mobile`
2. Run `npm run ios` to run the ios version. To run android versino, run `npm run android`
3. Ensure you have Expo Go installed on your mobile device. You may need to have an Expo account as well.
4. Ensure the development device (laptop) and your mobile device are on the same WiFi network.
5. After running `npm run ios` in step 2, the terminal should say something like 'Opening exp://172.16.11.65:8081 on [your device name]'. Open the browser on your mobile device, and go to the URL provided in the terminal.
6. That's it. You should be able to access the app on your phone.
