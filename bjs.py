# coding: utf-8
# py3
__author__ = 'odmen'
import sys
import string
import random
import gzip
import os
from datetime import datetime
import time

svg_to_path = ''
gziped = 0
sdate = ''


if len(sys.argv) == 1:
        print('''
-l Полный путь до лог-файла
-o Полный путь для сохранения svg
-d День в числовом значении
-g Открывать файл как .gz
--help Вывести эту справку
        ''')
        sys.exit()
for arg in sys.argv:
    # перебираем аргументы, переданные скрипту
    currindex = sys.argv.index(arg)
    # запоминаем индекс текущего выбранного аргумента
    if arg == "-l":
        # если текущий элемент - "-l"
        log_file_path = sys.argv[currindex + 1]
    if arg == "-o":
        # если текущий элемент - "-l"
        svg_to_path = sys.argv[currindex + 1]
    if arg == "-d":
        # если текущий элемент - "-l"
        sdate = sys.argv[currindex + 1]
    if arg == "-g":
        # если текущий элемент - "-l"
        gziped = 1
    if arg == "--help":
        print('''
-l Полный путь до лог-файла
-o Полный путь для сохранения svg
-d День в числовом значении
-g Открывать файл как .gz
--help Вывести эту справку
        ''')
        sys.exit()

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
# функция берет последовательность букв и цифр
# берет из этой последовательности случайные символы
# последовательность длинной 6 символов
# возвращает эту последовательность
    return ''.join(random.choice(chars) for _ in range(size))

def get_line_data(line, data):
    event_elems = {}
    # функция принимает на вход сырую строку лога и список колонок
    # для вывода (дата напрмиер или user-agent) в виде списка затем
    # пытается вытащить из строки все данные в соответсвии с нашим
    # форматом access лога apache если строка соответсвует этому
    # формату, то возвращает в виде json данные, перечисленные в
    # списке данных для вывода. притом json содержит статус выполняния
    # функции, если строка соответствовала формату лога, то в этом
    # json есть свойства с нужными данными, а если не соответствовала,
    # то в нем вся сломанная строка
    line = line.replace(b'\n',b'')
    # заменяем все символны перехода на новую строку в строке
    line_list = line.split(b'"')
    # разбиваем строку по двойной ковычке
    event_elems.clear()
    # сбрасываем список элеменов для вывода из фунции
    if len(line_list) == 7:
        # если список длиной 7 элементов (7 потому что блин так разбивается =) ), то
        idd = line_list[0].strip().split(b' ')
        # вытаскиваем все содержащие интересне данные из этого списка
        # тут ip, домен и дата ^
        ruh = line_list[1].strip().split(b' ')
        # тут тип запроса, url и версия http-протокола
        sd = line_list[2].strip().split(b' ')
        # тут статус ответа и длина отправленных данных
        if len(idd) == 5:
            # каждый их этих трех элементов проверяем на длину списка
            # и если длина не сооветствует ожидаемой, то считаем строку не валидной
            # поскольку будет не надежно использовать эти данные для анализа
            ip = idd[0]
            domain = idd[1]
            date = idd[3][1:]
        else:
            return {'code': "broken line", 'result': line}
        if len(ruh) == 3:
            # длина списка должна быть 3
            rtype = ruh[0]
            url = ruh[1]
            hver = ruh[2]
        else:
            return {'code': "broken line", 'result': line}
        if len(sd) == 2:
            # тут длина - 2. не больше и не меньше
            status = sd[0]
            dlen = sd[1]
        else:
            return {'code': "broken line", 'result': line}
        referer = line_list[3]
        ua = line_list[5]
        rtime = line_list[6]
        # если добрались до этого места, то понятно что строка валидна (по кол-ву колонок)
        # составляем json и заполняем его всеми данными
        # конечно не факт, что там все верно, но по крайней мере строка содержит столько колонок
        # сколько предусмотрено форматом лога
        json_data = {
            'ip': ip,
            'domain': domain,
            'date': date,
            'rtype': rtype,
            'url': b'"' + url + b'"',
            'hver': hver,
            'status': status,
            'dlen': dlen,
            'referer': referer,
            'ua': b'"' + ua + b'"',
            'rtime': rtime
        }
        for elem in data:
            # обходим список, переданный в функцию и вытаскиваем из json
            # элементы с такими ключами, какие перечислены в этом списке
            # добавляем их в другой список, он будет результатом работы функции
            event_elems[elem] = json_data[elem]
        return {'code': "valid line", 'result': event_elems}
    # возвращаем json, в нем два свойства:
    # code - статус работы функции, валидна строка или нет
    # result - тут или список с запрошенными элементами, или все сломанная строка
    else:
        return {'code': "broken line", 'result': line}

def bad_chart(svg_to_path, sdate):
    current_dir = os.getcwd()
    sorted_data = []
    bad_data = {}
    chart_data = []
    if gziped:
        log_file = gzip.open(log_file_path, 'r')
    else:
        log_file = open(log_file_path, 'rb')
    ckeck_list = ['status', 'date', 'rtime', 'url']
    mins = [ '%02d' % i for i in range(60) ]
    hours = [ '%02d' % i for i in range(24) ]
    for min in mins:
        for hour in hours:
            bad_data[sdate+':'+hour+':'+min] = 0
    for line in log_file:
        chck_psbl = 0
        lparse_res = get_line_data(line, ckeck_list)
        if lparse_res['code'] != 'broken line':
            event_data = lparse_res['result']
            event_data = {elem: event_data[elem].strip() for elem in event_data}
            if event_data['status'] != b'-':
                status = int(event_data['status'])
                if status > 499:
                    chck_psbl += 1
            if event_data['rtime'] != b'-':
                if float(event_data['rtime']) > 10:
                    chck_psbl += 1
            if chck_psbl:
                url = event_data['url']
                if (event_data['url'] != b'/robots.txt' and chck_psbl):
                    event_sdate = event_data['date'].split(b':')[0].decode("utf-8")
                    if event_sdate == sdate:
                        event_date = event_data['date'].decode("utf-8")[:-3]
                        bad_data[event_date] += 1
            else:
                pass
        else:
            pass
    for key in bad_data:
        sorted_data.append(key)
    sorted_data = sorted(sorted_data)
    for key in sorted_data:
        # {"date": key,"value": bad_data[key]}
        chart_data.append({"date": key,"value": bad_data[key]})
    print(chart_data)
    header = open(current_dir+'/temls/header.html').read()
    footer = open(current_dir+'/temls/footer.html').read()
    body = \
'''
  <body>
<script type="text/javascript">
var chart = AmCharts.makeChart("chartdiv", {
        "type": "serial",
        "theme": "none",
        "pathToImages": "http://www.amcharts.com/lib/3/images/",
        "dataDateFormat": "DD/MMM/YYYY:JJ:NN",
        "valueAxes": [{
            "axisAlpha": 0,
            "position": "left"
        }],
        "graphs": [{
      "id": "g1",
            "bullet": "round",
            "bulletBorderAlpha": 1,
            "bulletColor": "#FFFFFF",
            "bulletSize": 5,
            "hideBulletsCount": 50,
            "lineThickness": 2,
            "title": "red line",
            "useLineColorForBulletBorder": true,
            "valueField": "value"
        }],
        "chartScrollbar": {
      "graph": "g1",
      "scrollbarHeight": 30
    },
        "chartCursor": {
            "cursorPosition": "mouse",
            "pan": true
        },
        "categoryField": "date",
        "categoryAxis": {
            "parseDates": true,
            "dashLength": 1,
            "minorGridEnabled": true,
            "position": "top"
        },
        exportConfig:{
          menuRight: '20px',
          menuBottom: '50px',
          menuItems: [{
          icon: 'http://www.amcharts.com/lib/3/images/export.png',
          format: 'png'
          }]
        },
        "dataProvider": '''+str(chart_data)+'''
    }
);

chart.addListener("rendered", zoomChart);

zoomChart();
function zoomChart(){
    chart.zoomToIndexes(chart.dataProvider.length - 40, chart.dataProvider.length - 1);
}
</script>
  <div id="chartdiv"></div>
  </body>
'''

    result_html = open(current_dir+'/temls/result.html','w')
    result_html.write(header+body+footer)
    # header.close()
    # footer.close()
    result_html.close()

if not sdate:
    sys.exit('Не указан день')
elif svg_to_path == '':
    print('Не указан путь до сохраниения файла результата')
    print('Файл будет сохранен в "/tmp" со случайным именем')

bad_chart(svg_to_path, sdate)