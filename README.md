# Настройка проекта
Для начала работы необходимо создать новый проект, в который загрузить Engine.py и widgetClasses. После этого создайте в данной папке файл main.py и папки "images", "scenarios". В папке images будут размещаться изображения, в папке scenarios - сценарии. В каталоге scenarios создайте файл main.txt - точку входа для комикса. 

В main.py пропишите небольшую логику обработки игровых событий:
```
from Engine import Comix
import pygame

def main():
    WIDTH, HEIGHT = 1920, 1000
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Новелл')
    comix = Comix(screen, scenarios_root='scenarios/', staticfiles_root='images/')
    comix.process_frame()
    clock = pygame.time.Clock()

    while True:
        events = pygame.event.get()
        comix.process_event(events)

        comix.update_screen()
        clock.tick(40)
if __name__ == '__main__':
    main()
```

# Сценарии. Общее
Теперь можно приступить к написанию сценариев.
Сценарии пишутся в .txt файлах по фреймам. Пример кода (пишем в main.txt файле):
```
0
название_команды: параметр1, параметр2, параметр3;
1
название_команды: параметр1;
```
В самом начале прогружается 0 фрейм, срабатывает 1 команда с 3 параметрами. После чего программа ждёт клика игрока по экрану. По нажатию фрейм меняется на следующий, выполняется 2 команда с 1 параметром. 
Синтаксис:
###### Любая команда типа ключ:значение должна заканчиваться на ";"!
###### Перечесление параметров команды должно вестись через запятую!

# Команды
## background
Пример кода:
```
0
background:"image1.png";
```
Команда background позволяет добавить картинку на задний план. В качестве параметров принимает: относительный путь до изображения. Путь берётся смотря от папки images внутри проекта. то есть в данном пример изображение возьмётся по пути "текущий_проект/images/image1.png". Если разрешение картинки и разрешение окна не совпадает, то картинка растягивается до размеров окна.

## author
Пример кода:
```
0
author: top, "Текст рассказчика";
```
Команда author позволяет добавить речь рассказчика. В качестве параметров принимает: местоположение (top либо bottom), текст на панели.

## character
Пример кода:
```
0
character: [100,100], [200, 100], 30, "Текст персонажа";
```
Команда character позволяет добавить прямую речь внутриигровых персонажей. В качестве параметров принимает: позицию панели [x,y], размеры панели [width, height], размер шрифта (px), Текст персонажа.

## fnc
Пример кода:
```
0
fnc:goto(5);
```
Команда fnc позволяет запускать заготовленные функции, увеличивающие возможности и функционал игры. В качестве параметров принимает: функцию.

## choice
Пример кода:
```
0
choice: button1, "Выбор1", [100,100] | button2, "Выбор2", [200, 100];
button1: (здесь можно прописать любую функцию);
button2: (здесь можно прописать любую функцию);
```
Команда choice позволяет добавить выбор игрока и ветвление сюжета по нажатию на кнопку. В качестве параметров принимает: название callback-переменной, текст на кнопке, Позицию кнопки [x,y]. Название callback-переменной используется для обработки callback-функции кнопки. При нажатии на кнопку будет срабатывать соответствующая callback-переменной <b>функция</b>, прописанная в том же фрейме, где инициализируется choice.

# Функции.
Функции - это некоторый тип данных, способствующий увеличению возможностей и функционала игры.

## goto
Пример кода:
```
0
fnc:goto("lines/line1.txt", 10);
```
Функция goto goto позволяет перемещать исполнитель из одной части исполняемого файла в другую часть, либо из исполняемого файла в другой файл. В круглых скобках может указываться путь до файла в кавычках: goto("путь_до_файла"). В таком случае исполнитель перенесётся на нулевой фрейм файла по пути "текущий_проект/scenarios/путь_до_файла". Может указываться номер фрейма, на который нужно переместиться: goto(5). В таком случае исполнитель перенесётся на 5 фрейм текущего файла. Также можно переместиться на определённую строчку в определённом файле если сначала указать путь до файла а потом через запятую номер фрейма: goto("путь_до_файла", номер фрейма).
В примере выше исполнитель должен переместиться на 10 фрейм файла "текущий_проект/scenarios/lines/line1.txt".
