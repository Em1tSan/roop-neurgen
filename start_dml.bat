@echo off
call message.bat
pause

python -m pip install virtualenv

call install_dml.bat

call venv\Scripts\activate.bat
python run.py --execution-threads 1 --execution-provider dml --max-memory 16 --video-encoder libx264 --frame-processor face_swapper
pause

REM Упаковано и собрано телеграм каналом Neutogen News: https://t.me/neurogen_news
REM --gpu-threads 1 - Количество потоков для вашей видеокарты. В режиме DML можно выставить только один, увы.
REM --max-memory 8 - сколько вы готовы выделить оперативной памяти в гигабайтах
REM --video-encoder - Видео кодировщик. Можно выбрать libx264 или libx265
REM --frame-processor - выбор режима обработки. face_swapper - замена лица, face_enhancer - улучшение уже измененного лица через апскейлер
REM --execution-provider cuda - Наш бэкенд. Если у вас Nvidia - ставьте cuda, если Nvidia RTX 4000 - можете попробовать указать tensorrt.
