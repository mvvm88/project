from flask import Flask, render_template, request, redirect
import sqlite3
import hashlib
import time

app = Flask(__name__)

blocks = (
    (4, 10, 9, 2, 13, 8, 0, 14, 6, 11, 1, 12, 7, 15, 5, 3),
    (14, 11, 4, 12, 6, 13, 15, 10, 2, 3, 8, 1, 0, 7, 5, 9),
    (5, 8, 1, 13, 10, 3, 4, 2, 14, 15, 12, 7, 6, 0, 9, 11),
    (7, 13, 10, 1, 0, 8, 9, 15, 14, 4, 6, 12, 11, 2, 5, 3),
    (6, 12, 7, 1, 5, 15, 13, 8, 4, 10, 9, 14, 0, 3, 11, 2),
    (4, 11, 10, 0, 7, 2, 1, 13, 3, 6, 8, 5, 9, 12, 15, 14),
    (13, 11, 4, 1, 3, 15, 5, 9, 0, 10, 14, 7, 6, 8, 2, 12),
    (1, 15, 13, 0, 5, 7, 10, 4, 9, 2, 3, 14, 6, 11, 8, 12),
)
# ключ
key = 18318279387912387912789378912379821879387978238793278872378329832982398023031


#  получаем длину в битах
def bit_length(value):
    return len(bin(value)[2:])  # удаляем '0b' в начале


class Crypt(object):
    def __init__(self, key, sbox):
        assert bit_length(key) <= 256
        self._key = None
        self._subkeys = None
        self.key = key
        self.sbox = sbox

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, key):
        assert bit_length(key) <= 256
        # Для генерации подключей исходный 256-битный ключ разбивается на восемь 32-битных блоков: K1…K8.
        self._key = key
        self._subkeys = [(key >> (32 * i)) & 0xFFFFFFFF for i in range(8)]  # 8 кусков

    def _f(self, part, key):
        """Функция шифрования (выполняется в раудах)"""
        assert bit_length(part) <= 32
        assert bit_length(part) <= 32
        temp = part ^ key  # складываем по модулю
        output = 0
        # разбиваем по 4бита
        # в рез-те sbox[i][j] где i-номер шага, j-значение 4битного куска i шага
        # выходы всех восьми S-блоков объединяются в 32-битное слово
        for i in range(8):
            output |= ((self.sbox[i][(temp >> (4 * i)) & 0b1111]) << (4 * i))
            # всё слово циклически сдвигается влево (к старшим разрядам) на 11 битов.
        return ((output >> 11) | (output << (32 - 11))) & 0xFFFFFFFF

    def _decrypt_round(self, left_part, right_part, round_key):
        return left_part, right_part ^ self._f(left_part, round_key)

    def encrypt(self, msg):
        # "Шифрование исходного сообщения"

        def _encrypt_round(left, right, round_key):
            return right, left ^ self._f(right, round_key)

        assert bit_length(msg) <= 64
        # открытый текст сначала разбивается на две половины
        # (младшие биты — rigth_path, старшие биты — left_path)
        left_part = msg >> 32
        right_part = msg & 0xFFFFFFFF
        # Выполняем 32 рауда со своим подключом Ki
        # Ключи K1…K24 являются циклическим повторением ключей K1…K8 (нумеруются от младших битов к старшим).
        for i in range(24):
            left_part, right_part = _encrypt_round(left_part, right_part, self._subkeys[i % 8])
            # Ключи K25…K32 являются ключами K1…K8, идущими в обратном порядке.
        for i in range(8):
            left_part, right_part = _encrypt_round(left_part, right_part, self._subkeys[7 - i])
        return (left_part << 32) | right_part  # сливаем половинки вместе

    def decrypt(self, crypted_msg):
        """Дешифрование криптованого сообщения
        Расшифрование выполняется так же, как и зашифрование, но инвертируется порядок подключей Ki."""

        def _decrypt_round(left_part, right_part, round_key):
            return right_part ^ self._f(left_part, round_key), left_part

        assert bit_length(crypted_msg) <= 64
        left_part = crypted_msg >> 32
        right_part = crypted_msg & 0xFFFFFFFF
        for i in range(8):
            left_part, right_part = _decrypt_round(left_part, right_part, self._subkeys[i])
        for i in range(24):
            left_part, right_part = _decrypt_round(left_part, right_part, self._subkeys[(7 - i) % 8])
        return (left_part << 32) | right_part  # сливаем половинки вместе

@app.route('/', methods=["GET", "POST"])
def note():
    if request.method == 'POST' and list(request.form.values())[0]:
        global link
        link = hashlib.md5(list(request.form.values())[0].encode()).hexdigest()
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        text = list(request.form.values())[0]
        a = Crypt(key, blocks)
        new_text = [ord(i) for i in text]
        s = [str(a.encrypt(i)) for i in new_text]
        cursor.execute(f"INSERT INTO data VALUES(?, ?);", (link, ' '.join(s)))
        connection.commit()
        connection1 = sqlite3.connect('database2.db')
        cursor1 = connection1.cursor()
        cursor1.execute("INSERT INTO notes_data VALUES(?, ?, ?, ?);", (link, 2592000, '', 0))
        connection1.commit()
        connection2 = sqlite3.connect('database3.db')
        cursor2 = connection2.cursor()
        cursor2.execute("INSERT INTO notes_time VALUES(?, ?, ?);", (link, 2592000, time.time_ns()))
        connection2.commit()
        return render_template('edit.html', message='http://127.0.0.1:5000/notes/' + link)
    return render_template('edit.html')

@app.route('/notes/<note_link>', methods=['GET', 'POST'])
def get_note(note_link):
    connection1 = sqlite3.connect('database.db')
    cursor1 = connection1.cursor()
    connection3 = sqlite3.connect('database3.db')
    cursor3 = connection3.cursor()
    obj = cursor1.execute(f"SELECT * FROM data WHERE id='{note_link}'").fetchall()
    if len(obj):
        text = obj[0][1].split()
        a = Crypt(key, blocks)
        s1 = [chr(a.decrypt(int(i))) for i in text]
        connection = sqlite3.connect('database2.db')
        cursor = connection.cursor()
        k = cursor.execute(f'select * from notes_data where id="{note_link}"').fetchall()
        flag, pw = k[0][3], k[0][2]
        if flag:
            cursor.execute(f"DELETE FROM notes_data WHERE id='{note_link}'")
            connection.commit()
            cursor1.execute(f"DELETE FROM data WHERE id='{note_link}'")
            connection1.commit()
            cursor3.execute(f"DELETE FROM notes_time WHERE id='{note_link}'")
            connection3.commit()
            return render_template('get_note.html', message=''.join(s1))
        elif pw == '':
            new_flag = 1
            cursor.execute(f"UPDATE notes_data SET flag = '{new_flag}' WHERE id = '{note_link}'")
            cursor.execute(f"DELETE FROM notes_data WHERE id='{note_link}'")
            connection.commit()
            cursor1.execute(f"DELETE FROM data WHERE id='{note_link}'")
            connection1.commit()
            cursor3.execute(f"DELETE FROM notes_time WHERE id='{note_link}'")
            connection3.commit()
            return render_template('get_note.html', message=''.join(s1))
        else:
            return redirect(f'/{note_link}/check_access')
    return render_template('get_note.html', message='Такой заметки не существует')
    # return render_template('get_note.html')

@app.route('/set_access', methods=['GET', 'POST'])
def set():
    if request.method == 'POST':
        try:
            connection = sqlite3.connect('database.db')
            cursor = connection.cursor()
            note_id = cursor.execute(f"SELECT * FROM data").fetchall()[-1][0]
            print(note_id)
            time_list = list(request.form.values())
            print(time_list)
            note_time = int(time_list[0]) * 86400 + int(time_list[1]) * 3600 + int(time_list[2]) * 60 + int(time_list[3])
            connection1 = sqlite3.connect('database2.db')
            cursor1 = connection1.cursor()
            cursor1.execute(f"UPDATE notes_data SET time = '{note_time}' WHERE id = '{note_id}'")
            cursor1.execute(f"UPDATE notes_data SET password = '{time_list[4]}' WHERE id = '{note_id}'")
            connection1.commit()
            connection2 = sqlite3.connect('database3.db')
            cursor2 = connection2.cursor()
            cursor2.execute(f"UPDATE notes_time SET time = '{note_time}' WHERE id = '{note_id}'")
            cursor2.execute(f"UPDATE notes_time SET start_time = '{time.time_ns() // 10**9}' WHERE id = '{note_id}'")
            connection2.commit()
            return redirect('/')
        except:
            return render_template('set.html', message='Неправильно введенные данные')
    return render_template('set.html')

@app.route('/<note_link>/check_access', methods=['GET', 'POST'])
def check(note_link):
    if request.method == 'POST':
        try:
            psw = list(request.form.values())[0]
            connection = sqlite3.connect('database2.db')
            cursor = connection.cursor()
            real_psw = cursor.execute(f'select * from notes_data where id="{note_link}"').fetchall()[0][2]
            if psw == real_psw:
                new_flag = 1
                cursor.execute(f"UPDATE notes_data SET flag = '{new_flag}' WHERE id = '{note_link}'")
                connection.commit()
                return redirect(f'/notes/{note_link}')
            else:
                return render_template('check.html', message='Неправильный пароль')
        except:
            return render_template('check.html', message='Ошибка')
    return render_template('check.html')

app.run()

# connection = sqlite3.connect('database3.db')
# cursor = connection.cursor()
# cursor.execute('CREATE TABLE IF NOT EXISTS notes_time(id text, time integer, start_time integer);')
# print(cursor.execute('select * from notes_data').fetchall()[-1])
# print(cursor.execute('select * from notes_data where id="fcf688961714141ada12626df3f1d289"').fetchall()[0][2])
# cursor.execute("CREATE TABLE IF NOT EXISTS notes_data(id text, time integer, password text, flag integer);")
# connection.commit()
# connection = sqlite3.connect('database.db')
# cursor = connection.cursor()
# cursor.execute("CREATE TABLE IF NOT EXISTS data(id text, note text);")
# connection.commit()