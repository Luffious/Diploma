from django.shortcuts import render
from django.http import HttpResponse, FileResponse
from django.contrib import messages
from django.conf import settings
from fabric import Connection
from paramiko import AuthenticationException
import pandas as pd
import os
import csv
import time
from re import sub
from zipfile import ZipFile


def index(request):
    data = []
    if os.stat('main/static/main/csv/states.csv').st_size != 0:
        a = pd.read_csv('main/static/main/csv/states.csv', encoding='cp1251')
        b = pd.read_csv('main/static/main/csv/computing_machines.csv')
        pd.merge(b, a, on='hostname', how='outer').to_csv(
            'main/static/main/csv/data.csv', index=False, encoding='cp1251')
    with open('main/static/main/csv/data.csv', 'r', newline='') as d:
        data = list(csv.reader(d))[1:]
    with open('main/static/main/csv/tasks.csv', 'r', newline='', encoding='cp1251') as tasks:
        tasks = list(csv.reader(tasks))[1:]
    return render(request, 'main/index.html', {'data': data, 'tasks': tasks})


def ssh(request):
    with open('main/static/main/csv/states.csv', 'w', newline='') as states:
        writer = csv.writer(states)
        writer.writerow(['hostname', 'os', 'cputemp'])
        with open('main/static/main/csv/computing_machines.csv', 'r', newline='') as cm:
            midPC = {}
            with open('main/static/main/csv/middleman_PC.csv', 'r', newline='') as mid:
                reader = csv.DictReader(mid)
                for row in reader:
                    midPC = row
            middleman = Connection(host=midPC['ip'], user=midPC['host'], port=midPC['port'], connect_kwargs={
                                   'password': midPC['password']})
            reader = csv.DictReader(cm)
            for row in reader:
                ping = 'ping ' + row['ip'] + ' -c 5 -q'
                result = middleman.run(ping, warn=True).stdout.strip()
                prc_in = result.find('%')
                allpackets = result.find('100', prc_in - 4, prc_in)
                nopackets = result.find(' 0', prc_in - 4, prc_in)
                if (nopackets != -1):
                    try:
                        remotepc = Connection(host=row['ip'], user=row['hostL'], connect_kwargs={
                                              'password': row['passwordL']}, gateway=middleman)
                        result = remotepc.run(
                            'hostname', hide=True).stdout.strip()
                        temps = remotepc.run(
                            'sensors', hide=True).stdout.strip()
                        cpu = temps.find('+') + 1
                        degrees = temps.find('.', cpu)
                        temps = temps[cpu:degrees] + '\xb0C'
                        writer.writerow(
                            [sub('\D', '', result), 'Linux', temps])
                        remotepc.close()
                    except AuthenticationException:
                        remotepc = Connection(host=row['ip'], user=row['hostW'], connect_kwargs={
                                              'password': row['passwordW']}, gateway=middleman)
                        result = remotepc.run(
                            'hostname', hide=True).stdout.strip()
                        writer.writerow(
                            [sub('\D', '', result), 'Windows', '-'])
                        remotepc.close()
                elif (allpackets != -1):
                    writer.writerow([row['hostname'], '-', '-'])
                else:
                    writer.writerow(
                        [row['hostname'], 'Недоступно', '-'])
            middleman.close()
    index(request)
    return HttpResponse('''<html><script>window.location.replace('/');</script></html>''')


def wakeonlan(request, number):
    midPC = {}
    wolPC = {}
    with open('main/static/main/csv/middleman_PC.csv', 'r', newline='') as mid:
        reader = csv.DictReader(mid)
        for row in reader:
            midPC = row
    middleman = Connection(host=midPC['ip'], user=midPC['host'], port=midPC['port'], connect_kwargs={
                           'password': midPC['password']})
    with open('main/static/main/csv/wakeup_PC.csv', 'r', newline='') as wol:
        reader = csv.DictReader(wol)
        for row in reader:
            wolPC = row
    waker = Connection(host=wolPC['ip'], user=wolPC['host'], port=wolPC['port'], connect_kwargs={
                       'password': wolPC['password']}, gateway=middleman)
    with open('main/static/main/csv/computing_machines.csv', 'r', newline='') as cm:
        reader = csv.DictReader(cm)
        for row in reader:
            if row['hostname'] == number:
                wakeonlan = 'wakeonlan ' + row['mac']
                result = waker.run(wakeonlan).stdout.strip()
                waker.close()
                middleman.close()
                time.sleep(40)
                ssh(request)
                return HttpResponse('''<html><script>window.location.replace('/');</script></html>''')


def wakeall(request):
    midPC = {}
    wolPC = {}
    with open('main/static/main/csv/middleman_PC.csv', 'r', newline='') as mid:
        reader = csv.DictReader(mid)
        for row in reader:
            midPC = row
    middleman = Connection(host=midPC['ip'], user=midPC['host'], port=midPC['port'], connect_kwargs={
                           'password': midPC['password']})
    with open('main/static/main/csv/wakeup_PC.csv', 'r', newline='') as wol:
        reader = csv.DictReader(wol)
        for row in reader:
            wolPC = row
    waker = Connection(host=wolPC['ip'], user=wolPC['host'], port=wolPC['port'], connect_kwargs={
                       'password': wolPC['password']}, gateway=middleman)
    with open('main/static/main/csv/data.csv', 'r', newline='') as d:
        reader = csv.DictReader(d)
        for row in reader:
            if row['os'] == '-':
                wakeonlan = 'wakeonlan ' + row['mac']
                result = waker.run(wakeonlan).stdout.strip()
    waker.close()
    middleman.close()
    time.sleep(40)
    ssh(request)
    return HttpResponse('''<html><script>window.location.replace('/');</script></html>''')


def toLinux(request, number):
    midPC = {}
    with open('main/static/main/csv/middleman_PC.csv', 'r', newline='') as mid:
        reader = csv.DictReader(mid)
        for row in reader:
            midPC = row
    middleman = Connection(host=midPC['ip'], user=midPC['host'], port=midPC['port'], connect_kwargs={
                           'password': midPC['password']})
    with open('main/static/main/csv/computing_machines.csv', 'r', newline='') as cm:
        reader = csv.DictReader(cm)
        for row in reader:
            if row['hostname'] == number:
                winPC = Connection(host=row['ip'], user=row['hostW'], port=row['port'], connect_kwargs={
                    'password': row['passwordW']}, gateway=middleman)
                result = winPC.run('shutdown /r', hide=True).stdout.strip()
                winPC.close()
                middleman.close()
                time.sleep(80)
                ssh(request)
                return HttpResponse('''<html><script>window.location.replace('/');</script></html>''')


def send(request, number):
    if request.method == 'POST':
        midPC = {}
        with open('main/static/main/csv/middleman_PC.csv', 'r', newline='') as mid:
            reader = csv.DictReader(mid)
            for row in reader:
                midPC = row
        middleman = Connection(host=midPC['ip'], user=midPC['host'], port=midPC['port'], connect_kwargs={
            'password': midPC['password']})
        with open('main/static/main/csv/computing_machines.csv', 'r', newline='') as cm:
            reader = csv.DictReader(cm)
            for row in reader:
                if row['hostname'] == number:
                    orca = Connection(host=row['ip'], user=row['hostL'], port=row['port'], connect_kwargs={
                        'password': row['passwordL']}, gateway=middleman)
                    foldername = request.POST['foldername']
                    inp = request.FILES['fileinp']
                    xyz = request.FILES['filexyz']
                    dir = 'orca_tasks/' + foldername
                    check = inp.name.replace('inp', 'xyz')
                    if (check == xyz.name):
                        messages.info(
                            request, 'Имена файла .xyz и .inp не должны совпадать!')
                        return HttpResponse('''<html><script>window.location.replace('/');</script></html>''')
                    else:
                        result = orca.run(
                            '[ -d ' + dir + ' ] && echo \'Directory exists.\'', warn=True, encoding='utf-8').stdout.strip()
                        if (result == 'Directory exists.'):
                            messages.info(request, 'Такая папка уже есть!')
                            return HttpResponse('''<html><script>window.location.replace('/');</script></html>''')
                        else:
                            result = orca.run('mkdir -p ' + dir,
                                              encoding='utf-8').stdout.strip()
                            orca.put(xyz, dir)
                            orca.put(inp, dir)
                            with orca.cd(dir):
                                outname = inp.name.replace('inp', 'out')
                                orca.run('sed -i -e \'$a\\\' ' +
                                         inp.name, encoding='utf-8', hide=True)
                                orca.run('/opt/orca303/orca ' + inp.name + ' > ' +
                                         outname, asynchronous=True, encoding='utf-8')
                                with open('main/static/main/csv/tasks.csv', 'a', newline='') as tasks:
                                    writer = csv.writer(tasks)
                                    dot = inp.name.find('.')
                                    filename = inp.name[0:dot]
                                    writer.writerow(
                                        [number, foldername, filename, 'создан', ''])
                                orca.close()
                                middleman.close()
                            return HttpResponse('''<html><script>window.location.replace('/');</script></html>''')


def calculations(request, number, foldername, filename):
    midPC = {}
    with open('main/static/main/csv/middleman_PC.csv', 'r', newline='') as mid:
        reader = csv.DictReader(mid)
        for row in reader:
            midPC = row
    middleman = Connection(host=midPC['ip'], user=midPC['host'], port=midPC['port'], connect_kwargs={
        'password': midPC['password']})
    count, temp = 0, 0
    with open('main/static/main/csv/tasks.csv', 'r', newline='') as t:
        reader = csv.reader(t)
        for row in reader:
            if row[0] == number and row[1] == foldername and row[2] == filename:
                count = temp - 1
            temp += 1
    with open('main/static/main/csv/computing_machines.csv', 'r', newline='') as cm:
        reader = csv.DictReader(cm)
        for row in reader:
            if row['hostname'] == number:
                orca = Connection(host=row['ip'], user=row['hostL'], port=row['port'], connect_kwargs={
                    'password': row['passwordL']}, gateway=middleman)
                dir = 'orca_tasks/' + foldername
                result = orca.run('ps aux | grep \'cd ' + dir + '\'',
                                  encoding='utf-8', warn=True, hide=True).stdout.strip()
                state = result.find('bash -c cd ' + dir)
                if state == -1:
                    out = filename + '.out'
                    xyz = filename + '.xyz'
                    hess = filename + '.hess'
                    inp = filename + '.inp'
                    dirname = number + foldername + filename
                    path = os.path.normcase(settings.MEDIA_ROOT + '/' + dirname + '/')
                    with orca.cd(dir):
                        result = orca.run('ls ' + out,
                                          encoding='utf-8', warn=True, hide=True).stdout.strip()
                        if result != '':
                            orca.get(dir + '/' + out, path)
                        result = orca.run('ls ' + xyz,
                                          encoding='utf-8', warn=True, hide=True).stdout.strip()
                        if result != '':
                            orca.get(dir + '/' + xyz, path)
                        result = orca.run('ls ' + hess,
                                          encoding='utf-8', warn=True, hide=True).stdout.strip()
                        if result != '':
                            orca.get(dir + '/' + hess, path)
                        result = orca.run('ls ' + inp,
                                          encoding='utf-8', warn=True, hide=True).stdout.strip()
                        if result != '':
                            orca.get(dir + '/' + inp, path)
                        result = orca.run('tail -2 ' + out,
                                          encoding='utf-8', hide=True).stdout.strip()
                    normal = result.find('NORMALLY')
                    if normal != -1:
                        with open(path + inp) as inpfile:
                            lines = inpfile.readlines()
                        opt, optts = False, False
                        for line in lines:
                            if 'OptTS' in line:
                                optts = True
                            elif 'Opt' in line:
                                opt = True
                        with open(path + out) as outfile:
                            lines = outfile.readlines()
                        lines = ''.join(lines)
                        lines = lines[lines.rfind(
                            'VIBRATIONAL FREQUENCIES') + 49:lines.rfind('NORMAL MODE') - 16]
                        lines = ''.join(
                            (c for c in lines if c.isdecimal() or c == '.' or c == '\n' or c == '-'))
                        lines = lines.split()
                        for i in range(len(lines)):
                            if i < 9:
                                lines[i] = lines[i][1:-2]
                                lines[i] = float(lines[i])
                            elif i >= 9 and i <= 98:
                                lines[i] = lines[i][2:-2]
                                lines[i] = float(lines[i])
                            else:
                                lines[i] = lines[i][3:-2]
                                lines[i] = float(lines[i])
                        negative = 0
                        neg_numbers = ''
                        for numbers in lines:
                            if numbers < 0:
                                negative += 1
                                neg_numbers += str(numbers) + '; '
                        if negative == 0 and opt:
                            tasks = pd.read_csv(
                                'main/static/main/csv/tasks.csv', encoding='cp1251')
                            tasks.loc[count,
                                      'status'] = 'завершён успешно'
                            tasks.to_csv(
                                'main/static/main/csv/tasks.csv', index=False, encoding='cp1251')
                        elif negative > 0 and opt:
                            tasks = pd.read_csv(
                                'main/static/main/csv/tasks.csv', encoding='cp1251')
                            if negative == 1:
                                tasks.loc[count,
                                          'status'] = 'завершён неуспешно'
                                tasks.loc[count, 'extra'] = ', ' + str(
                                    negative) + ' отрицательное значение: ' + neg_numbers[:-2]
                            elif negative >= 2 and negative <= 4:
                                tasks.loc[count,
                                          'status'] = 'завершён неуспешно'
                                tasks.loc[count, 'extra'] = ', ' + str(
                                    negative) + ' отрицательных значения: ' + neg_numbers[:-2]
                            elif negative >= 5:
                                tasks.loc[count,
                                          'status'] = 'завершён неуспешно'
                                tasks.loc[count, 'extra'] = ', ' + str(
                                    negative) + ' отрицательных значений: ' + neg_numbers[:-2]
                            tasks.to_csv(
                                'main/static/main/csv/tasks.csv', index=False, encoding='cp1251')
                        elif negative == 1 and optts:
                            tasks = pd.read_csv(
                                'main/static/main/csv/tasks.csv', encoding='cp1251')
                            tasks.loc[count,
                                      'status'] = 'завершён успешно'
                            tasks.loc[count, 'extra'] = ', ' + str(
                                negative) + ' отрицательное значение: ' + neg_numbers[:-2]
                            tasks.to_csv(
                                'main/static/main/csv/tasks.csv', index=False, encoding='cp1251')
                        elif negative != 1 and optts:
                            tasks = pd.read_csv(
                                'main/static/main/csv/tasks.csv', encoding='cp1251')
                            if negative == 0:
                                tasks.loc[count,
                                          'status'] = 'завершён неуспешно'
                                tasks.loc[count, 'extra'] = ', ' + str(
                                    negative) + ' отрицательных значений: ' + neg_numbers[:-2]
                            elif negative >= 2 and negative <= 4:
                                tasks.loc[count,
                                          'status'] = 'завершён неуспешно'
                                tasks.loc[count, 'extra'] = ', ' + str(
                                    negative) + ' отрицательных значения: ' + neg_numbers[:-2]
                            elif negative >= 5:
                                tasks.loc[count,
                                          'status'] = 'завершён неуспешно'
                                tasks.loc[count, 'extra'] = ', ' + str(
                                    negative) + ' отрицательных значений: ' + neg_numbers[:-2]
                            tasks.to_csv(
                                'main/static/main/csv/tasks.csv', index=False, encoding='cp1251')
                        with ZipFile(path + dirname + '.zip', 'w') as zip:
                            zip.write(path + out, out)
                            zip.write(path + xyz, xyz)
                            zip.write(path + hess, hess)
                            zip.write(path + inp, inp)
                        os.remove(path + out)
                        os.remove(path + xyz)
                        os.remove(path + hess)
                        os.remove(path + inp)
                    else:
                        tasks = pd.read_csv(
                            'main/static/main/csv/tasks.csv', encoding='cp1251')
                        tasks.loc[count,
                                  'status'] = 'прерван до завершения'
                        tasks.to_csv('main/static/main/csv/tasks.csv',
                                     index=False, encoding='cp1251')
                        with ZipFile(path + dirname + '.zip', 'w') as zip:
                            if os.path.exists(path + out):
                                zip.write(path + out, out)
                            if os.path.exists(path + xyz):
                                zip.write(path + xyz, xyz)
                            if os.path.exists(path + hess):
                                zip.write(path + hess, hess)
                            if os.path.exists(path + inp):
                                zip.write(path + inp, inp)
                        if os.path.exists(path + out):
                            os.remove(path + out)
                        if os.path.exists(path + xyz):
                            os.remove(path + xyz)
                        if os.path.exists(path + hess):
                            os.remove(path + hess)
                        if os.path.exists(path + inp):
                            os.remove(path + inp)
                else:
                    tasks = pd.read_csv(
                        'main/static/main/csv/tasks.csv', encoding='cp1251')
                    tasks.loc[count, 'status'] = 'считается'
                    tasks.to_csv('main/static/main/csv/tasks.csv',
                                 index=False, encoding='cp1251')
                orca.close()
                count += 1
    middleman.close()
    return HttpResponse('''<html><script>window.location.replace('/');</script></html>''')


def get(request, number, foldername, filename):
    with open('main/static/main/csv/tasks.csv', 'r', newline='') as tasks:
        reader = csv.DictReader(tasks)
        for row in reader:
            if row['hostname'] == number and row['foldername'] == foldername and row['filename'] == filename:
                dirname = number + foldername + filename
                path = os.path.normcase(settings.MEDIA_ROOT + '/' + dirname + '/')
                filepath = path + dirname + '.zip'
                file = open(filepath, 'rb')
                return FileResponse(open(filepath, 'rb'))


def remove(request, number, foldername, filename):
    midPC = {}
    with open('main/static/main/csv/middleman_PC.csv', 'r', newline='') as mid:
        reader = csv.DictReader(mid)
        for row in reader:
            midPC = row
    middleman = Connection(host=midPC['ip'], user=midPC['host'], port=midPC['port'], connect_kwargs={
        'password': midPC['password']})
    pc = {}
    with open('main/static/main/csv/computing_machines.csv', 'r', newline='') as cm:
        reader = csv.DictReader(cm)
        for row in reader:
            if row['hostname'] == number:
                pc = row
    once = True
    with open('main/static/main/csv/tasks.csv', 'r', newline='') as tasks:
        taskreader = csv.DictReader(tasks)
        for taskrow in taskreader:
            if taskrow['hostname'] == number and taskrow['foldername'] == foldername and taskrow['filename'] == filename and once:
                once = False
                orca = Connection(host=pc['ip'], user=pc['hostL'], port=pc['port'], connect_kwargs={
                    'password': pc['passwordL']}, gateway=middleman)
                dir = 'orca_tasks/' + taskrow['foldername']
                result = orca.run('ps aux | grep \'cd ' + dir +
                                  '\'', encoding='utf-8', warn=True, hide=True).stdout.strip()
                state = result.find('bash -c cd ' + dir)
                if state == -1:
                    result = orca.run(
                        'rm -r ' + dir, encoding='utf-8', warn=True, hide=True).stdout.strip()
                orca.close()
    middleman.close()
    with open('main/static/main/csv/tasks.csv', 'r', newline='') as t:
        reader = csv.reader(t)
        with open('main/static/main/csv/temp.csv', 'w', newline='') as temp:
            writer = csv.writer(temp)
            for task in reader:
                if task[0] == number and task[1] == foldername and task[2] == filename:
                    pass
                else:
                    writer.writerow(
                        [task[0], task[1], task[2], task[3], task[4]])
    os.replace('main/static/main/csv/temp.csv',
               'main/static/main/csv/tasks.csv')
    dirname = number + foldername + filename
    path = os.path.normcase(settings.MEDIA_ROOT + '/' + dirname)
    os.remove(os.path.normcase(path + '/' + dirname + '.zip'))
    os.rmdir(path)
    return HttpResponse('''<html><script>window.location.replace('/');</script></html>''')
