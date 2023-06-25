python -m venv venv
call venv\Scripts\activate.bat
python -m pip install ./whl/insightface-0.7.3-cp310-cp310-win_amd64.whl
pip install -r requirements_dml.txt
