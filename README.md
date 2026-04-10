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
