# -*- coding: utf8 -*-
"""
Обработка HTTP запросов приложения upload.

Формирование страницы загрузки.
Обработка AJAX запроса загрузки файла.
Обработка AJAX запроса текущей информации о процессах.

"""
import os
import pickle
from datetime import datetime, timedelta

import redis 

from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.conf import settings

from upload.forms import UploadFileForm
from upload.tasks import fileUploadTask
from upload.models import BigFile

BASE_DIR = settings.BASE_DIR

REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT
REDIS_DB = settings.REDIS_DB
EXPIRE_INTERVAL = settings.EXPIRE_INTERVAL
FILE_LIST_VIEW_SIZE = settings.FILE_LIST_VIEW_SIZE


def index(request):
    """
    Страница загрузки файла.

    Предоставляет форму загрузки файла,
    список текущих процессов
    и список последних обработанных файлов.
    """
    form = UploadFileForm()
    results = _results()
    return render(request, "index.html",
                            {'form': form,
                             'file_list': results['file_list'],
                             'process_list': results['process_list']})


def _results():
    """
    Создание единого набора данных для
    формирования страницы и AJAX запроса.

    Читает информацию о загружаемых и обрабатываемых файлах
    из базы Redis и создаёт список текущих процессов.
    Удаляет из базы Redis записи, с момента создания которых
    прошло время, превышающее указанный интервал.

    Читает информацию об обработанных файлах из модели
    BigFile и создаёт список последних обработанных файлов.

    """
    file_list = [
          {'id': bf.id,
           'name': bf.name,
           'ready': bf.ready,
           'result': bf.result
          }
          for bf in BigFile.objects.filter(ready=True)
                           .order_by('-id').all()[:FILE_LIST_VIEW_SIZE]
         ]
    rdb = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    process_list = []
    expire_time = datetime.now() - timedelta(seconds=EXPIRE_INTERVAL)
    for key in rdb.keys():
        data = pickle.loads(rdb.get(key))
        if not 'ctime' in data or data['ctime'] < expire_time:
            rdb.delete(key)
        else:
            process_list.append(data)
    return {'file_list': file_list,
            'process_list': process_list}


def get_results(request):
    """
    Обработчик AJAX запроса текущей информации о процессах.

    Отсылает список текущих процессов
    и список последних обработанных файлов
    в формате JSON.

    """
    results = _results()
    return JsonResponse(results)


def upload(request):
    """
    Обработчик AJAX запроса загрузки файла.

    Если форма валидна, запускает процесс загрузки файла,
    иначе, возвращает информацию об ошибках формы.
    
    """
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            _upload_file(request.FILES['uploadfile'])
            return JsonResponse({'ok': ''}, content_type='text/html')
        else:
            return JsonResponse({'error': dict(form.errors)})
    else:
        return JsonResponse({'error': 'POST method expected'})


def _upload_file(sf):
    """
    Загрузка файла.

    Создаёт новый экземпляр модели BigFile
    и добавляет его id к имени файла.

    Вызывает функцию fileUploadTask, определённую как задача Celery,
    которая выполняет загрузку файла.
    Задача вызывается синхронно, поскольку не получается сериализовать
    файловый объект из запроса.

    """
    name = os.path.join(BASE_DIR, 'files', sf.name)
    bf = BigFile(name=name)
    bf.save()
    name = "{}_{}".format(name, bf.id)
    bf.name = name
    bf.save()
    fileUploadTask(bf.id, sf, name)

