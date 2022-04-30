# Граппер Telegram
____
## Функционал
Получение новых постов с фильтрацией и заменой текста, для последующей пересылки в чаты соц. сети ВКонтакт

### Список задач
- [X] Пересылка вложеных файлов (фото\видео)
- [ ] Добавить отправку опросов
- [ ] Пофиксить баг пересылаемых сообщений (пересылает по отдельности)

## Установка
``` python
pip install vk-api
```
``` python
pip install telethon
```
``` python
pip install requests
```
создать файл `confing.py` с токенами и настройками
пример файла с описанием `confing-example.py`

## Запуск
После установки и добавления всех токенов, требуется аривторизовать бота, советую для этог использовать `TokenActivation.py` т.к. в рабочем файле она не проходит, ещё не разобрался почему.