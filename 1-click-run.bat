@echo off
call message.bat
pause

python -m pip install virtualenv

call install.bat

set PYTORCH_CUDA_ALLOC_CONF=garbage_collection_threshold:0.8,max_split_size_mb:512
set CUDA_MODULE_LOADING=LAZY

call venv\Scripts\activate.bat
python run.py --gpu-threads 10 --gpu-vendor nvidia --max-memory 16000 --upscale
pause

:: Упаковано и собрано телеграм каналом Neutogen News: https://t.me/neurogen_news Все обновления будут там
:: Пояснения:
:: Перед запуском стоят переменные, нацеленные на оптимизацию работы видеопамяти или ускорение обработки данных. В принципе, можете удалить если они вас смущают.
:: --max-memory 8000 - тут пишите сколько готовы выделить оперативной памяти в мегабайтах. У меня стоит 8000 мегабайт. Иногда, при слишком больших значениях, может вылезть ошибка по памяти, в таком случае лучше снизить занчение.
:: --gpu-threads 8 - Количество потоков GPU. Если у вас слабая видеокарта, рекомендую начать со значения 1 и потихоньку подниматься выше.
