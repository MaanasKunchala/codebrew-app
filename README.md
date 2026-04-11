DREAMERS
## Setup

### Backend

cd codebrew-app<br>
python -m venv venv<br>

#### Recommendation is to run the Virtual Envvironment. Please use OS-specific commands.
##### For Mac
source venv/bin/activate
##### For Windows
./venv/Scripts/activate

cd backend <br>
pip install -r requirements.txt <br>
uvicorn app:app --reload <br>

### Frontend
cd frontend <br>
python3 -m http.server 5500 <br>

## To set up db on your machine:
python init_db.py <br>
python seed_season_data.py <br>

### After running, close VM
deactivate <br>
