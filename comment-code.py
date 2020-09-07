
# ипорт библиотек
import xml.etree.ElementTree as XmlElementTree
import httplib2
import uuid
from config import ** *  # не синтаксис питона - просто скрытые данные

** *_HOST = '***'       # переменаня создержащие имя хоста
** *_PATH = '/***_xml'  # путь до данных
CHUNK_SIZE = 1024 ** 2  # часть (чанк) 1024 в степени 2



# Функция для перевода речи в текст.
# Parameters:
#    filename: файл
#    bytes: байткод
#    request_id: uuid - пользовательский id / id каталога
#    topic: название топика
#    lang: код языка
#    key: Api ключ
# Returns:
#    text: текст песни/аудиофайла.

def speech_to_text(filename=None, bytes=None, request_id=uuid.uuid4().hex, topic='notes', lang='ru-RU',
                   key=** * _API_KEY):


    # если передан файл, читаем его побайтово
    if filename:
        with open(filename, 'br') as file:
            bytes = file.read()
    # если данные небыли переданы или прочитаны выкидываем ощибку
    if not bytes:
        raise Exception('Neither file name nor bytes provided.')

    bytes = convert_to_pcm16b16000r(in_bytes=bytes)

    # формируем url и подставляем данные
    url = _PATH + '?uuid=%s&key=%s&topic=%s&lang=%s' % (
        request_id,
        key,
        topic,
        lang
    )

    # разбиваем на сегменты/части наши данные (1024 в степени 2)
    chunks = read_chunks(CHUNK_SIZE, bytes)


    # создаем соединение с хостом
    connection = httplib2.HTTPConnectionWithTimeout(***_HOST)

    # подключаемся
    connection.connect()

    # сообщаем, что мы передаем через POST
    connection.putrequest('POST', url)

    # передаем заголовки
    connection.putheader('Transfer-Encoding', 'chunked')
    connection.putheader('Content-Type', 'audio/x-pcm;bit=16;rate=16000')
    connection.endheaders()


    # цикл отправки по частям наших данных
    for chunk in chunks:
        # длинна чанка в 16ричной системе исчислания с обрезанием 0x
        connection.send(('%s\r\n' % hex(len(chunk))[2:]).encode())
        # сам чанк
        connection.send(chunk)
        # \r\n
        connection.send('\r\n'.encode())

    # завершающий пакет
    connection.send('0\r\n\r\n'.encode())

    # получение ответа от api
    response = connection.getresponse()

    # если все отправилось, то читаем ответ
    if response.code == 200:
        response_text = response.read()
        # полученную строку загоняем в XML
        xml = XmlElementTree.fromstring(response_text)
        # парсим наш xml
        # если поле 'success' == 1
        if int(xml.attrib['success']) == 1:
            # аля флаг проверки, получили ли мы текст или нет -inf
            max_confidence = - float("inf")
            text = ''

            # перебираем xml и если условие проходит, забираем текст
            for child in xml:
                if float(child.attrib['confidence']) > max_confidence:
                    text = child.text
                    max_confidence = float(child.attrib['confidence'])

            # если флаг отработатл, возвращаем текст, если нет - то кидаем ошибку
            if max_confidence != - float("inf"):
                return text
            # далее выкидваем ошибки если на каком-то из условий что-то пошло не так.
            else:
                raise SpeechException('No text found.\n\nResponse:\n%s' % (response_text))
        else:
            raise SpeechException('No text found.\n\nResponse:\n%s' % (response_text))
    else:
        raise SpeechException('Unknown error.\nCode: %s\n\n%s' % (response.code, response.read()))


сlass SpeechException(Exception):
    pass
