class DuplicationVinError(Exception):
    def __str__(self):
        return "Автомобиль с данным VIN-номером уже существует в бд"


class ModelNotExistError(Exception):
    def __str__(self):
        return "Модель вносимого автомобиля не существует в бд"


class DuplicationModelError(Exception):
    def __str__(self):
        return "Данная модель уже существует в бд"
