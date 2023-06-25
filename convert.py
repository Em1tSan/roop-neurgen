# Импортируем необходимые библиотеки
import onnx
from onnxconverter_common import float16

# Загружаем onnx модель
model = onnx.load("genderage.onnx")

# Конвертируем модель в fp16
model_fp16 = float16.convert_float_to_float16(model)

# Сохраняем модель в fp16
onnx.save(model_fp16, "genderage_fp16.onnx")
