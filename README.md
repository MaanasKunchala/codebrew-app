DREAMERS
## Setup

### Backend

cd codebrew-app
python -m venv venv
source venv/bin/activate
cd backend
pip install -r requirements.txt
uvicorn app:app --reload

### Frontend
cd frontend
python3 -m http.server 5500

## To set up db on your machine:
python init_db.py
python seed_season_data.py

### After running, close VM
deactivate
