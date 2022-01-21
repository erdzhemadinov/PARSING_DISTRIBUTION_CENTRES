# Yandex maps parser

[//]: # (## _The Last Markdown Editor, Ever_)

Данный инструмент позволяет извлечь базовую информацию об организациях, 
по запросу, например "Ozon, пункты выдачи" по регионам РФ в сервисе [Яндекс карты](https://yandex.ru/maps/?ll=84.163264%2C61.996842&z=3). 

## Перечень информации:

- Название компании
- Адрес
- Широта (неоходимо поместить токен в файл *"token.txt"* для [Google API](https://developers.google.com/maps/documentation/geocoding/overview))
- Долгота (неоходимо поместить токен в файл *"token.txt"* для [Google API](https://developers.google.com/maps/documentation/geocoding/overview))
- Регион расположения


## Особенности

- Парсинг информации по регионам по релевантному для пользователя запросу
- Подмена USER-AGENT (как способ ухода от блокировок)
- Обогащение геометками за счёт геокодинга
- Запись либо в xlsx, либо в базу(в разработке)
- Выбор одного из двух браузеров 
- С примером выгрузки можно ознакомиться в папке ./outputs

##  Предподготовка
> Для работы необходим токен, получить который можно [здесь](https://developers.google.com/maps/documentation/geocoding/start).
> Также для работы необходим браузер Firefox 96.0 или Chrome 89. 
> 
> В противном случае 
> вам необходимо самостоятельно найти и скачать driver Selenium для  [Chrome](https://chromedriver.chromium.org/downloads)
> или [Firefox](https://github.com/mozilla/geckodriver/releases) по указанным ссылкам. Версия driver
> и версия браузера должны быть идентичными.


## Dependecies

Для начала установите необходимые библиотеки из файла requirements.txt
```sh
pip install -r requirements.txt
```

## Parameters

Для запуска скрипта используются следующие параметры

```sh
-b --browser (string)
```

Браузер для парсина. Пареметр может принимать оно из двух значений "firefox" или "chrome". 
Обязательный параметр. Тип str


```sh
-q --query (string)
```

Запрос для поисковой строки Яндекс карт для поиска всех объектов в определенной области.
Обязательный параметр тип str


```sh
--range_left (string) 
```
Левая граница для регионов помогает взять slice(подвыборку) регионов, числовые коды регионов находятся в файле
*"regions.xlsx"* . Необзязательный, значение по умолчанию 0, тип int

```sh
--range_right (string) 
```
Правая граница для регионов помогает взять slice(подвыборку) регионов, числовые коды регионов находятся в файле
*"regions.xlsx"* . Необзязательный, значение по умолчанию 86, тип int


```sh
-t --token (string)
```

Токен для гугл API. Необходимо получить з



## Examples 
```sh
python main.py --browser="firefox" --query="Ozon, пункты выдачи"
```

## License

MIT

**Free Software, Hell Yeah!**

