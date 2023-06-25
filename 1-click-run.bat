set PATH=ffmpeg

set PYTORCH_CUDA_ALLOC_CONF=garbage_collection_threshold:0.8,max_split_size_mb:512
set CUDA_MODULE_LOADING=LAZY
set OMP_NUM_THREADS=1

call venv\Scripts\activate.bat
python run.py --gpu-threads 8 --gpu-vendor nvidia --max-memory 32000
pause

REM Упаковано и собрано телеграм каналом Neutogen News: https://t.me/neurogen_news
REM --gpu-threads N - Количество потоков для вашей видеокарты. Слишком большое значение может вызвать ошибки или наоборот, снизить производительность. 4 потока потребляют примерно 5.5-6 Gb VRAM, 8 потоков - 10 Gb VRAM, но пиковое потребление бывает выше. 
REM --tensorrt для активации TensorRT ускорения (Nvidia RTX 20xx, 30xx, 40xx) (экспериментально)
REM --autolaunch для включения/выключения автозапуска UI
REM --share_gradio которая генерирует ссылку для доступа из сети
REM --max_num_faces N - для установки максимального количества лиц для замены. 
