@echo off
cd /d %~dp0
if not exist python\myenv (
  py -3 -m venv python\myenv
)
python\myenv\Scripts\python -m pip install -r python\requirements.txt
pushd python
myenv\Scripts\python manage.py migrate
myenv\Scripts\python seed_demo.py
start "h5-api" myenv\Scripts\python manage.py runserver 0.0.0.0:8010
popd
if not exist h5\node_modules call npm --prefix h5 install
if not exist admin\node_modules call npm --prefix admin install
start "h5-web" cmd /c "cd /d %~dp0h5 && npm run dev"
start "h5-admin" cmd /c "cd /d %~dp0admin && npm run dev"
echo H5 http://localhost:5173
echo Admin http://localhost:5174
echo API http://localhost:8010/api/v1/health
