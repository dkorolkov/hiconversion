# -*- coding: utf8 -*-
"""
Задачи для асинхронной обработки файлов.

Функции вызываются через Celery и осуществляют
загрузку и парсинг файлов в асинхронном режиме.

Для хранения промежуточных результатов используется Redis.
Задача создаёт запись Redis информацией о процессе:
  имя файла
  тип процесса (upload - загрузка, parsing - парсинг)
  степень готовности задачи в процентах
  время начала выполнения задачи
Ключ записи состоит из типа процесса и идентификатора файла,
разделённых двоеточием.
Идентификатор файла --  поле id модели BigFile.
Web-приложение читает данные из Redis для отображения на странице.

"""
from os import stat
from datetime import datetime
import pickle

from celery import Celery
import redis 

from django.conf import settings

from upload.models import BigFile

REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT
REDIS_DB = settings.REDIS_DB

app = Celery('bigfiles')


@app.task()
def fileUploadTask(bf_id, sf, dest_name):
    """
    Асинхронная загрузка файла.

    bf_id id из модели BigFiles
    sf объект загружаемого файла из запроса
    dest_name полный путь для сохранения файла

    Функция создаёт запись Redis с информацией о процессе загрузки.
    В процессе загрузки функция вычисляет процент загрузки и
    перезаписывает информацию с текущим значением процента.
    После окончания загрузки запись удаляется.

    """
    sz = sf.size
    rdb = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT,
                            db=REDIS_DB)
    key = 'upload:{}'.format(bf_id)
    start_time = datetime.now()
    rdb.set(key, pickle.dumps({'key': key,
                               'name': dest_name,
                               'process': 'upload',
                               'progress': 0,
                               'ctime': start_time}))
    sum_size = 0
    with open(dest_name, 'wb') as df:
        for chunk in sf.chunks():
            df.write(chunk)
            sum_size += len(chunk)
            rdb.set(key, pickle.dumps({
                           'key': key,
                           'name': dest_name,
                           'process': 'upload',
                           'progress': int(sum_size/sz*100),
                           'ctime': start_time}))
    rdb.delete(key)
    fileProcessTask.delay(bf_id)


@app.task()
def fileProcessTask(bf_id):
    """
    Асинхронный парсинг файла.

    bf_id id из модели BigFiles

    Функция создаёт запись Redis с информацией о процессе парсинга.
    В процессе загрузки функция вычисляет процент выполнения и
    перезаписывает информацию с текущим значением процента.
    После окончания загрузки запись удаляется.

    """
    bf = BigFile.objects.get(id=bf_id)
    rdb = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT,
                            db=REDIS_DB)
    key = 'parsing:{}'.format(bf_id)
    start_time = datetime.now()
    rdb.set(key, pickle.dumps({'key': key,
                               'name': bf.name,
                               'process': 'parsing',
                               'progress': 0,
                               'ctime': start_time}))
    sz = stat(bf.name).st_size
    char_counter = 0
    with open(bf.name) as f:
        sum_size = 0
        while True:
            s = f.read(1024)
            if len(s) == 0:
                break
            # Подсчитываем символы в цикле, чтобы сымитировать парсинг
            for c in s:
                char_counter += 1
            sum_size += len(s)
            rdb.set(key, pickle.dumps({
                           'key': key,
                           'name': bf.name,
                           'process': 'count',
                           'progress': int(sum_size / sz * 100),
                           'ctime': start_time}))
    rdb.delete(key)
    bf.result = char_counter
    bf.ready = True
    bf.save()

