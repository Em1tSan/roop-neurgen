@echo off
call message.bat
pause

python -m pip install virtualenv

call install.bat

set PYTORCH_CUDA_ALLOC_CONF=garbage_collection_threshold:0.8,max_split_size_mb:512
set CUDA_MODULE_LOADING=LAZY
set CUDA_PATH=venv\Lib\site-packages\torch\lib

call venv\Scripts\activate.bat
python run.py --execution-threads 4 --execution-provider cuda --max-memory 16
pause

REM Упаковано и собрано телеграм каналом Neutogen News: https://t.me/neurogen_news
REM --gpu-threads N - Количество потоков для вашей видеокарты. Слишком большое значение может вызвать ошибки или наоборот, снизить производительность. 4 потока потребляют примерно 5.5-6 Gb VRAM, 8 потоков - 10 Gb VRAM, но пиковое потребление бывает выше. 
REM --max-memory 8 - сколько вы готовы выделить оперативной памяти в гигабайтах
REM --frame-processor - выбор режима обработки. face_swapper - замена лица, face_enhancer - улучшение уже измененного лица через апскейлер
REM --execution-provider cuda - Наш бэкенд. Если у вас Nvidia - ставьте cuda, если Nvidia RTX 4000 - можете попробовать указать tensorrt.
