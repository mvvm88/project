import sqlite3
import time

i = 0

while True:
    t1 = time.time_ns()
    connection6 = sqlite3.connect('database3.db')
    cursor6 = connection6.cursor()
    lst = cursor6.execute('select * from notes_time').fetchall()
    if len(lst):
        i = i % len(lst)
        # print(t1 // 10 ** 9 - lst[i][2], lst[i][0])
        if t1 // 10 ** 9 - lst[i][2] >= lst[i][1]:
            connection4 = sqlite3.connect('database2.db')
            cursor4 = connection4.cursor()
            connection5 = sqlite3.connect('database.db')
            cursor5 = connection5.cursor()
            connection6 = sqlite3.connect('database3.db')
            cursor6 = connection6.cursor()
            cursor6.execute(f"DELETE FROM notes_time WHERE id='{lst[i][0]}'")
            connection6.commit()
            cursor5.execute(f"DELETE FROM data WHERE id='{lst[i][0]}'")
            connection5.commit()
            cursor4.execute(f"DELETE FROM notes_data WHERE id='{lst[i][0]}'")
            connection4.commit()
            del lst[i]
        else:
            i += 1