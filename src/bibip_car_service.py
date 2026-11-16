from models import (
    Car,
    CarFullInfo,
    CarStatus,
    Model,
    ModelSaleStats,
    Sale,
    BaseModel,
)
import json
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from sortedcontainers import SortedDict
from exceptions import (
    DuplicationVinError,
    ModelNotExistError,
    DuplicationModelError,
    VinNotExistError,
    CarAvailabilityError,
)
from collections import Counter

Path("data").mkdir(exist_ok=True)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CAR_FILE = PROJECT_ROOT / "data" / "cars.txt"
CAR_INDEX_FILE = PROJECT_ROOT / "data" / "cars_index.txt"

MODEL_FILE = PROJECT_ROOT / "data" / "models.txt"
MODEL_INDEX_FILE = PROJECT_ROOT / "data" / "models_index.txt"


LINE_LENGTH = 500


class CarService:
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = (
            root_directory_path  # root_directory_path = PROJECT_ROOT / "data"
        )
        self._line_length = 500

        # Атрибуты для задания 1
        self._cars_file = f"{self.root_directory_path}/cars.txt"
        self._cars_index_file = f"{self.root_directory_path}/cars_index.txt"
        self._models_file = f"{self.root_directory_path}/models.txt"
        self._models_index_file = (
            f"{self.root_directory_path}/models_index.txt"
        )

        self._car_index = self._load_index(self._cars_index_file)
        self._model_index = self._load_index(
            self._models_index_file, key_type=int
        )

        self._models = self._load_model()

        # Атрибуты для задания 2
        self._sales_file = f"{self.root_directory_path}/sales.txt"
        self._sales_index_file = f"{self.root_directory_path}/sales_index.txt"

        self._sales_index = self._load_index(self._sales_index_file)

    # По models.py id моделей машины является первичным ключом, но таблица с моделями является словарем,
    # то есть повторяться наименование модели не может
    # через внутренний метод _load_model создаем список с моделями из таблицы моделей для проверки
    def _load_model(self) -> list[str]:
        model_list = []
        with open(
            self._models_file, "a+", encoding="utf-8", newline="\n"
        ) as f:
            f.seek(0)
            for line in f:
                if not line.strip():
                    continue
                model = Model.model_validate_json(line.strip())
                model_list.append(model.name)
        return model_list

    def _load_index(
        self, file_path: str, key_type: type[str] | type[int] = str
    ) -> SortedDict:

        with open(file_path, "a+", encoding="utf-8", newline="\n") as f:
            try:
                f.seek(0)
                raw_data = json.load(f)
                return SortedDict(
                    {key_type(k): v for k, v in raw_data.items()}
                )
            except json.JSONDecodeError:
                return SortedDict()

    # def _save_index(self, file_path: str, index_data: SortedDict) -> None:
    #     with open(file_path, "w", encoding="utf-8", newline="\n") as f:
    #         json.dump(index_data, f, ensure_ascii=False, indent=2)
    #     return None
    def _add(
        self,
        file_path: str,
        file_path_index: str,
        data_string: BaseModel,
        data_attr: str,
        index_data: SortedDict,
    ) -> SortedDict:
        key = getattr(data_string, data_attr)
        with open(file_path, "a+", encoding="utf-8", newline="\n") as f:
            f.write(
                data_string.model_dump_json().ljust(self._line_length) + "\n"
            )
            line_number = (f.tell() // (self._line_length + 1)) - 1
            index_data[key] = line_number
        with open(file_path_index, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        return index_data

        # нет смысла выводить отдельный get, так как может понадобится вывести
        # несколько объектов в массив, а это означает, что в цикле отдельная функция
        # будет каждый раз открывать и закрывать файл,
        # а нам достаточно только один раз выгрузить в память
        # и преобразовывать строки в объекты оттуда
        # UPDATE: есть смысл делать отдельный get, просто добавим условие
        # при которой возвращает либо один объект, либо список объектов
        # UPDATE2: зачем мне mode_list, если проверка на значение key уже разделяет метод

    def _get[T: BaseModel](
        self,
        file_path: str,
        index_data: SortedDict,
        cls: type[T],
        key: str | int | None,
        # mode_list: bool = False,
    ) -> list[T] | T | None:
        # raise NotImplementedError
        if key is not None:
            try:
                line_number = index_data[key]
            except KeyError:
                return None
            # if mode_list is False:
            with open(file_path, "r", encoding="utf-8", newline="\n") as f:
                f.seek(line_number * (self._line_length + 1))
                obj = cls.model_validate_json(f.read(500).strip())
            return obj
        result = []
        with open(file_path, "r", encoding="utf-8", newline="\n") as f:
            for line in f:
                if not line.strip():
                    continue
                obj = cls.model_validate_json(line.strip())
                result.append(obj)
        return result

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        # raise NotImplementedError

        try:
            if model.name in self._models:
                raise DuplicationModelError
        except DuplicationModelError:
            print(f"Модель с именем {model.name} уже есть в бд")

        else:
            # raise NotImplementedError
            self._add(
                self._models_file,
                self._models_index_file,
                model,
                "id",
                self._model_index,
            )
        return model

    # Задание 1. Сохранение автомобилей и моделей
    # index_data = self._car_index или self._model_index

    def add_car(self, car: Car) -> Car:
        # raise NotImplementedError
        try:
            if car.vin in self._car_index:
                raise DuplicationVinError
            if car.model not in self._model_index:
                raise ModelNotExistError
        except DuplicationVinError:
            print(f"Автомобиль с VIN-номером {car.vin} уже существует в бд")
            return car
        except ModelNotExistError:
            print(
                f"Модель с индексом {car.model} вносимого автомобиля не существует в бд"
            )

        else:

            # with open(
            #     self.root_directory_path + "/cars.txt",
            #     "a+",
            #     encoding="utf-8",
            #     newline="\n",
            # ) as f:
            #     # Сериализуем объект car с атрибутами в json строку и добавляем достаточно пробелов
            #     # Чтобы получить длину всей строки 500 и добавляем символ переноса строки
            #     f.write(car.model_dump_json().ljust(self._line_length) + "\n")
            #     line_number = (f.tell() // (self._line_length + 1)) - 1
            #     self._car_index[str(car.vin)] = line_number
            self._add(
                self._cars_file,
                self._cars_index_file,
                car,
                "vin",
                self._car_index,
            )
        return car

    # Задание 2. Сохранение продаж.
    def sell_car(
        self, sale: Sale
    ) -> Car | None:  # Пока добавим возможность возвращать ничего
        # raise NotImplementedError
        try:
            if sale.car_vin in self._sales_index:
                raise DuplicationVinError
            if sale.car_vin not in self._car_index:
                raise VinNotExistError
        except DuplicationVinError:
            print(f"Автомобиль с Vin-номером {sale.car_vin} уже был продан")
            return None
        except VinNotExistError:
            print(
                f"Автомобиль с Vin-номером {sale.car_vin} не существует в бд"
            )
            return None
        else:
            line_number = self._car_index[sale.car_vin]
            with open(
                self._cars_file, "r+", encoding="utf-8", newline="\n"
            ) as f:
                f.seek(line_number * (self._line_length + 1))
                car = Car.model_validate_json(
                    f.read(self._line_length).strip()
                )
                # try:
                #     if car.status == CarStatus(
                #         "reserve"
                #     ) or car.status == CarStatus("delivery"):
                #         raise CarAvailabilityError
                # except CarAvailabilityError:
                #     print(
                #         f"Статус автомобиля {car.status} не позволяет его продать"
                #     )
                #     return car
                # else:

                car.status = CarStatus.sold
                f.seek(line_number * (self._line_length + 1))
                f.write(car.model_dump_json().ljust(self._line_length) + "\n")
                self._add(
                    self._sales_file,
                    self._sales_index_file,
                    sale,
                    "car_vin",
                    self._sales_index,
                )

        return car

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        # raise NotImplementedError
        result = []
        with open(self._cars_file, "r", encoding="utf-8", newline="\n") as f:
            for line in f:
                if not line.strip():
                    continue
                car = Car.model_validate_json(line.strip())
                if car.status == status:
                    result.append(car)
        return result

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        # raise NotImplementedError
        # line_number = self._car_index[vin]
        car = self._get(self._cars_file, self._car_index, Car, vin)
        if car is None:
            # print("car = ", car)
            return None
        model = self._get(
            self._models_file, self._model_index, Model, car.model
        )
        sale = self._get(self._sales_file, self._sales_index, Sale, vin)
        if model is None:
            # print("model = ", model)
            return None
        if sale is None:
            car_full_info = CarFullInfo(
                vin=vin,
                car_model_name=model.name,
                car_model_brand=model.brand,
                price=car.price,
                date_start=car.date_start,
                status=car.status,
            )
            return car_full_info
        car_full_info = CarFullInfo(
            vin=vin,
            car_model_name=model.name,
            car_model_brand=model.brand,
            price=car.price,
            date_start=car.date_start,
            status=car.status,
            sales_date=sale.sales_date,
            sales_cost=sale.cost,
        )
        return car_full_info
        # with open(self._cars_file, 'r', encoding='utf-8', newline='\n') as f:
        #     f.seek(line_number * (self._line_length + 1))
        #     car = Car.model_validate_json(f.read(500).lstrip())
        # line_number = self._model_index[car.model]
        # with open(self._models_file, 'r', encoding='utf-8', newline='\n') as f:
        #     f.seek(line_number * (self._line_length + 1))
        #     model = Model.model_validate_json(f.read(500).lstrip())
        # with open(self._sales_index, 'r', encoding='utf-8')

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car | None:
        # raise NotImplementedError
        car = self._get(self._cars_file, self._car_index, Car, vin)
        if car is None:
            return None
        car.vin = new_vin
        line_number = self._car_index[vin]
        del self._car_index[vin]
        self._car_index[new_vin] = line_number
        with open(self._cars_file, "r+", encoding="utf-8", newline="\n") as f:
            f.seek(line_number * (self._line_length + 1))
            f.write(car.model_dump_json().ljust(self._line_length) + "\n")
        return car

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car | None:
        # raise NotImplementedError
        with open(self._sales_file, "r+", encoding="utf-8", newline="\n") as f:
            for line_number, line in enumerate(f):
                if not line.strip():
                    continue
                sale = Sale.model_validate_json(line.strip())
                if sale.sales_number == sales_number:
                    break
            sale.is_deleted = True
            # line_number = (f.tell() // (self._line_length + 1)) - 1
            f.seek(line_number * (self._line_length + 1))
            f.write(sale.model_dump_json().ljust(self._line_length) + "\n")
            with open(
                self._cars_file, "r+", encoding="utf-8", newline="\n"
            ) as f:
                line_number = self._car_index[sale.car_vin]
                f.seek(line_number * (self._line_length + 1))
                car = Car.model_validate_json(f.read(500).strip())
                car.status = CarStatus.available
                f.seek(line_number * (self._line_length + 1))
                f.write(car.model_dump_json().ljust(self._line_length) + "\n")

            return car
        return None

    # Как же я долго промучился с этим заданием, так как там требуется
    # не только обычная сортировка, но сортировка по дате продажи
    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats] | None:
        # raise NotImplementedError
        car_list = self.get_cars(status=CarStatus.sold)
        if not car_list:
            return None
        sales_list = self._get(
            self._sales_file, self._sales_index, Sale, key=None
        )

        vin_to_date = {sale.car_vin: sale.sales_date for sale in sales_list}
        stats_by_model: dict[int, dict] = {}
        for car in car_list:
            sale_date = vin_to_date.get(car.vin)

            if car.model not in stats_by_model:
                stats_by_model[car.model] = {
                    "count": 1,
                    "earliest_date": sale_date,
                }
            else:
                stats_by_model[car.model]["count"] += 1
                if sale_date < stats_by_model[car.model]["earliest_date"]:
                    stats_by_model[car.model]["earliest_date"] = sale_date
        sorted_models = sorted(
            stats_by_model.items(),
            key=lambda item: (-item[1]["count"], item[1]["earliest_date"]),
        )
        model_list = self._get(
            self._models_file, self._model_index, Model, key=None
        )
        models_by_id = {model.id: model for model in model_list}
        result = []
        for model_id, data in sorted_models[:3]:
            model = models_by_id.get(model_id)
            if model:
                result.append(
                    ModelSaleStats(
                        car_model_name=model.name,
                        brand=model.brand,
                        sales_number=data["count"],
                    )
                )

        return result


if __name__ == "__main__":

    # Загружаем индексацию сразу в память, чтобы каждый раз не открывать файл
    # при инициализации методов сохранения
    # и выгрузки информации из бд и сохраняем при завершении программы
    # with open(MODEL_INDEX_FILE, "r", encoding="utf-8") as f:
    #     try:
    #         raw_models_data = json.load(f)
    #         models_index = SortedDict(
    #             {str(k): v for k, v in raw_models_data.items()}
    #         )
    #     except json.JSONDecodeError:
    #         models_index = SortedDict()

    # with open(CAR_INDEX_FILE, "r", encoding="utf-8") as f:
    #     try:
    #         raw_car_data = json.load(f)
    #         car_index = SortedDict(
    #             {str(k): v for k, v in raw_car_data.items()}
    #         )
    #     except json.JSONDecodeError:
    #         car_index = SortedDict()

    model3 = Model(id=3, name="Sportage", brand="Kia")
    car1 = Car(
        vin="bla1231",
        model=3,
        price=Decimal(400.0),
        date_start=datetime(2026, 12, 1, 12, 15, 00),
        status=CarStatus("available"),
    )
    car2 = Car(
        vin="5mo0092921",
        model=20,
        price=Decimal(1337.0),
        date_start=datetime(2026, 12, 1, 12, 15, 00),
        status=CarStatus("sold"),
    )
    sale1 = Sale(
        sales_number="1",
        car_vin="bla1231",
        sales_date=datetime.today(),
        cost=Decimal(400.0),
    )
    service = CarService(f"{PROJECT_ROOT}/data")
    service.add_model(model3)
    service.add_car(car1)
    service.add_car(car2)
    service.sell_car(sale1)
    # print(service.get_cars(CarStatus.sold))

    # print(service.get_car_info(car1.vin))
    # print(service.top_models_by_sales())
