import json
from pathlib import Path
import models as md
from datetime import datetime
from decimal import Decimal
from sortedcontainers import SortedDict
from exceptions import DuplicationVinError

Path("data").mkdir(exist_ok=True)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CAR_FILE = PROJECT_ROOT / "data" / "cars.txt"
CAR_INDEX_FILE = PROJECT_ROOT / "data" / "cars_index.txt"
LINE_LENGTH = 500


car_index = SortedDict()


def main():

    car = md.Car(
        vin="bla1231",
        model=3,
        price=Decimal(400.0),
        date_start=datetime(2026, 12, 1, 12, 15, 00),
        status=md.CarStatus("available"),
    )
    car2 = md.Car(
        vin="4mo0092921",
        model=20,
        price=Decimal(1337.0),
        date_start=datetime(2026, 12, 1, 12, 15, 00),
        status=md.CarStatus("sold"),
    )
    # print(car)
    # Загружаем строку с данными машины в бд
    with open(CAR_INDEX_FILE, "a+", encoding="utf-8") as f:
        raw_data = json.load(f)
        car_index2 = SortedDict({str(k): v for k, v in raw_data.items()})
        print(f'car_index = {car_index2}')
    with open(CAR_FILE, "a+", encoding="utf-8") as f:
        f.write(car.model_dump_json().ljust(500) + "\n")
        vin = car.vin
        print("car1 =", f.tell())
        line_number = (f.tell() // (LINE_LENGTH + 1)) - 1
        
        car_index[str(vin)] = line_number
        print(line_number)
    with open(CAR_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(car_index, f, ensure_ascii=False, indent=2)
    with open(CAR_FILE, "a+", encoding="utf-8") as f:
        f.write(car2.model_dump_json().ljust(500) + "\n")
        print(f.tell())
        vin2 = car2.vin
        line_number2 = (f.tell() // (LINE_LENGTH + 1)) - 1
        car_index[str(vin2)] = line_number2
    with open(CAR_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(car_index, f, ensure_ascii=False, indent=2)
    # Берем из файла строку с машиной
    with open(CAR_FILE, "a+", encoding="utf-8") as f:
        f.seek(line_number * (501))
        val = f.read(500).strip()
    car_out = md.Car.model_validate_json(val)
    print(type(car_out))
    print(car_out.vin)
    # Загружаем индексы позиции строки машины с конкретным вин номером
    with open(CAR_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(car_index, f, ensure_ascii=False, indent=2)
    # Пробуем обратно выгрузить вин
    with open(CAR_INDEX_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
        print(f'raw_data = {raw_data.items()}')
        restored_sd = SortedDict({str(k): v for k, v in raw_data.items()})
        print("car2 id of string =", restored_sd[vin2])
    # Пробуем найти и выгрузить строку, содержащую конкретный vin номер, зная номер этой строки
    with open(CAR_FILE, "r+", encoding="utf-8") as f:
        f.seek(int(restored_sd[vin2]) * 501)
        car_out = md.Car.model_validate_json(f.read(500).strip())
        print("Цена до изменения= ", car_out.price)
        # Пробуем перезаписать данные в существующей машине
        car_out.price = Decimal(1488.0)
        f.seek(int(restored_sd[vin2]) * 501)
        f.write(car_out.model_dump_json().ljust(500) + "\n")

    with open(CAR_FILE, "a+", encoding="utf-8") as f:
        try:
            
            if car.vin in restored_sd:
                raise DuplicationVinError
            else:
                f.write(car.model_dump_json().ljust(500) + "\n")
                vin = car.vin
                print("car1 =", f.tell())
                line_number = (f.tell() // (LINE_LENGTH + 1)) - 1
                f.write(car2.model_dump_json().ljust(500) + "\n")
                print(f.tell())
                vin2 = car2.vin
                line_number2 = (f.tell() // (LINE_LENGTH + 1)) - 1
                car_index[str(vin)] = line_number
                car_index[str(vin2)] = line_number2
                print(line_number)
        except DuplicationVinError:
            print(f'Автомобиль с Vin-номером {car.vin} уже существует в бд')


if __name__ == "__main__":
    main()
