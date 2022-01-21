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
- Запись либо в xlsx, либо в базу, либо в оба источника(конфигурационная информация должна находится в файле см. пример файла config.json)
- Выбор одного из двух браузеров Chrome или Firefox
- Автообновление данных в базе
- С примером выгрузки можно ознакомиться в папке ./outputs. Выгрузки сохраняются в папку с запросом в качестве имени файла

UPD: Пока нет уверенности в том, что данные выгружаемые из Яндекс.Карт полноценны


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

Браузер для парсинга. Пареметр может принимать оно из двух значений "firefox" или "chrome". 
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
*"regions.xlsx"*. Необязательный, значение по умолчанию 0, тип int

```sh
--range_right (string) 
```
Правая граница для регионов помогает взять slice(подвыборку) регионов, числовые коды регионов находятся в файле
*"regions.xlsx"*. Необязательный, значение по умолчанию 86, тип int


```sh
-t --token (string)
```

Токен для Google API. Необходимо получить [здесь](https://developers.google.com/maps/documentation/geocoding/start).



```sh
-s --save_place (string)
```

Место для сохранения результатов. Параметр может принимать оно из трёх значений "excel", "database" или "both". 
Для атрибутов "database" и "both" требуется наличие конфигурационного файла для подключения к базе данных (пример файла *config.json*).
Можно использовать именно его.
Обязательный параметр. Тип str

Столбцы в базе данных должны иметь аналогичные имена и типы:


- ADDRESSES | VARCHAR(512)
- TYPE_PP | VARCHAR(256)
- LAT | DOUBLE
- LON | DOUBLE
- REGION | VARCHAR(256)
- DATE_OF_LOADING | DATE
- DATE_OF_LOADING_FIRST | DATE
- COMPANY_NAME | VARCHAR(256)

## Examples 
```sh
python main.py --browser="firefox" --query="Ozon, пункты выдачи" --token="aezakmiAEZAKMIaezakmi" --save_place="both"
```
Для извлечения информации по всем регионам и сохранением в Excel и базу с использованием Firefox

```sh
python main.py --browser="chrome" --query="Ozon, пункты выдачи" --range_left=10 --range_right=15 --token="aezakmiAEZAKMIaezakmi" --save_place="excel"
```

Для сохранения в Excel для регионов с 10 по 15 (в списке *regions.xlsx*) с использованием браузера Chrome


## License

FREE

**Free Software, Hell Yeah!**

