#! /usr/bin/env python3.4
import sys
import matplotlib.pyplot as plot
import re
from dateutil import parser
import math
import types

#################################################
#
#   definovanie tried pre jednotlive tabulky
#
##################################################
def AddLog(arg1, arg2):
    r = 10**(arg1/10) + 10**(arg2/10)
    result = 10 * math.log(r, 10)
    return result

#WCDMA PN Search Edition 2
class Table1:
    
    def __init__(self, rx_car0_agc0, rx_car0_agc1, rx_car1_agc0, rx_car1_agc1, date):
        rx_car0_agc0 = rx_car0_agc0
        rx_car0_agc1 = rx_car0_agc1
        rx_car1_agc0 = rx_car1_agc0
        rx_car1_agc1 = rx_car1_agc1
        self.date = date
    def parse_row(self, row):
        res = re.match(r'RX_CARR0_AGC_0\s*=\s*(.*)dBm', row)
        if res:
           self.rx_car0_agc0 = float(re.sub(',','.',res.group(1)))
        res = re.match(r'RX_CARR0_AGC_1\s*=\s*(.*)dBm', row)
        if res:
           self.rx_car0_agc1 = float(re.sub(',','.',res.group(1)))
        res = re.match(r'RX_CARR1_AGC_0\s*=\s*(.*)dBm', row)
        if res:
            self.rx_car1_agc0 = float(re.sub(',','.',res.group(1)))
        res = re.match(r'RX_CARR1_AGC_1\s*=\s*(.*)dBm', row)
        if res:
            self.rx_car1_agc1 = float(re.sub(',','.',res.group(1)))
        
    def parse(self, table, row):
        global cells
        global active_set
        global monitoring_set  
        
        if self.rx_car0_agc1:
            rssi_primary = AddLog(self.rx_car0_agc0, self.rx_car0_agc1)
        if hasattr(self, 'rx_car1_agc1'):
            if self.rx_car1_agc1:
                rssi_secondary = AddLog(self.rx_car1_agc0, self.rx_car1_agc1)
        else:
            rssi_secondary = None 

        for row in table:
            row = row.split('|')
            r=re.sub(' ','',row[1])    
            if len(r) > 0:
                
                psc = int(row[3])  
                carrier = row[2]
               
                cell = {}
                
                cell['primary_RSSI'] = rssi_primary
                if rssi_secondary:
                    cell['secondary_RSSI'] = rssi_secondary
                 
               #zisti ACTIVE SET a MONITORING SET 
                if 'ASET' in row[4]:
                    active_set[psc] = True         
                if 'MSET' in row[4]:
                    monitoring_set[psc] = True
                
                if not psc in cells:
                    cells[psc] = cell
                    ecno[psc] = []
                    rscp[psc] = [] 

#HS Decode Status Log Packet with Data Edition 3     
class Table2:
    def __init__(self, date):
       self.date = date 
    def parse_row(self, row):
        return
    def parse(self,table, count):
        global dl_l1
        global dl_l2
        dl_ack = 0
        dl_nak = 0

        if count == 1:
            for row in table:
                row = row.split('|')    
                data = re.sub(' ', '', row[4])
                
                if len(data) > 0:
                    data = int(data)
                    if row[3] == 'PASS':
                        dl_ack += data
                    elif row[3] == 'FAIL':              
                        dl_nak += data
        
        elif count == 2:
            return
        
        dl_l1 += dl_ack + dl_nak
        dl_l2 += dl_ack

#EUL Combined L1/MAC
class Table3:
    def __init__(self, date):
        self.date = date 
    def parse_row(self, row):
        global tti_10
        global tti_2
        
        res = re.match(r'\s*TTI\s*=(.*)ms', row)
        if res:
            r = re.sub(' ','', res.group(1))
            if r == '10' : 
                tti_10 += 1
            elif r == '2':
                tti_2 +=1
    def tti():
        
        if tti_10 == 0:
            return 'TTI=10ms sa nevyskytuje'

        else:
            return (tti_2/tti_10)
    
    def parse(self,table, count):
        global ul_l1
        global ul_l2
        global max_tbs       
        global ul_peak
        global ul_l1_speed
        global ul_mac_speed
        global error_rate
        ul_ack = 0
        ul_nak = 0

        if count == 2:
            for row in table:
                row = row.split('|')
                if re.match(r'\s+ACK',row[22]):
                    if len(row[20]) > 0: 
                        ul_ack += int(row[20])
                elif re.match(r'\s+NAK', row[22]):
                    if len(row[20]) > 0:
                        ul_nak += int(row[20])
                if len(row[20]) > 0 and int(row[20]) > max_tbs:
                    max_tbs = int(row[20])                  
            
            #peak    XXX not sure which TTI use
            if ((ul_ack + ul_nak) / (0.01 * len(table)))  > ul_peak:
                ul_peak = (ul_ack + ul_nak) /( 0.01 * len(table))
            l = [] 
            l.append(self.date)
            l.append((ul_ack + ul_nak) / (0.010 * len(table)))
            ul_l1_speed.append(l)
            l2 = []
            l2.append(self.date)
            l2.append((ul_ack) / (0.01 * len(table)))            
            ul_mac_speed.append(l2)
           
            l3 = []
            l3.append(self.date)
            l3.append(ul_nak/(ul_ack + ul_nak))
            error_rate.append(l3) 
        
        elif count == 1:
            return

        ul_l1 += ul_ack + ul_nak
        ul_l2 += ul_ack

#WCDMA Temporal Analysis Edition 2
class Table4:
    def __init__(self, date):
        self.date = date 
    def parse_row(self, row):
        return
    def parse(self, table, count):
        #prehladavame tabulku cislo 2
        if count == 2:
            
            ec = {}

            for row in table:
                row = row.split('|')
                psc = int(row[5])
                if not psc in ec:
                    ec[psc] = []
                
                ec[psc].append(float(re.sub(',','.',row[4])))
            
            if not psc in cells:
                return
            else:
                res = 0.0
                for val in ec[psc]:
                    res += 10**(val/10)
                #res obsahuje ecno
                res = math.log(res, 10) * 10
                l = []
                l.append(self.date)
                l.append(res)
                ecno[psc].append(l)
                
                #scitavanie logaritmov je nasobenie v linearnej mierke 
                l2 = []
                l2.append(self.date)
                l2.append(res + cells[psc]['primary_RSSI'])                
                rscp[psc].append(l2)

#EUL Link Statistics
class Table5:
    def parse_row(self, row):
        #XXX 
        global limit_power
        global limit_sg
        global limit_buffer
        #res = re.match(r'\s*Number Of Times Poewr Limited.*', row)
        if 'Number of Times Power Limited' in row:
            res = row.split(' ')
            limit_power += int(res[6])
            return
        if 'Number of SG Limited' in row:
            res = row.split(' ')
            limit_sg += int(res[5])
        if 'Number of Buffer Limited' in row:
            res = row.split(' ')
            limit_buffer += int(res[5])
        
    def parse(self, table, row):
        return

########################################
#
#   definovanie premennych
#
########################################
dl_l1 = 0
dl_l2 = 0
ul_l1 = 0
ul_l2 = 0
ul_peak = 0
tti_10 = 0
tti_2 = 0
max_tbs = 0
limit_sg = 0
limit_buffer = 0
limit_power = 0

ul_l1_speed = []
ul_mac_speed = []
error_rate = []
ecno = {}
rscp = {}

cells = {}
active_set = {}
monitoring_set = {}
device_EUL_category = 1
hlavicka = False
telo = False
record = None
rec = []
rec_count = 0


#########################################################
#
#   koniec definicie premennych a vlastnych tried
#   zaciatok parsovania
#
#########################################################

#otvorenie suboru, z ktoreho budeme citat data
f = open(sys.argv[1], encoding='utf-8')

#prechadzanie jednotlivymi riadkami suboru
for line in f:
    
    line = re.sub('\s*\|-' ,'--', line)
    
    #ak sme na zaciatku tabulky, je tam datum, cas a jej nazov... 
    res = re.match(r'^(\d{4}\s+\w{3}\s+[^\[]*)\[(..)\]\s+(\w+)\s+(.*)$', line)
    if res:
        date = parser.parse(res.group(1).strip(' '))
        date = str(date).split(' ') 
        rec_count = 0

        if res.group(4) == 'WCDMA PN Search Edition 2':
            record = Table1(None, None, None, None, date[1])
        elif res.group(4) == 'HS Decode Status Log Packet with Data Edition 3':
            record = Table2(date[1])
        elif res.group(4) == 'EUL Combined L1/MAC':
            record = Table3(date[1])
        elif res.group(4) == 'WCDMA Temporal Analysis Edition 2':
            record = Table4(date[1])
        elif res.group(4) == 'EUL Link Statistics':
            record = Table5()
        else:
            record = None
        continue
    
    #ak nam zacina novy zaznam, zvysime pocitadlo zaznamov o 1, a stary zaznam zahodine
    res = re.match(r'^\s*-+', line)
    if res:
        #print('yes' + res.group(0))
        rec = []
        if hlavicka:
            hlavicka = False
            telo = True
        else:
            hlavicka = True
            telo = False
        continue
    
    #ak tabulka konci, spracujeme ju
    res = re.match(r'^\s*\|', line)
    if not res and (hlavicka or telo):
        rec_count += 1
        if record:
            record.parse(rec, rec_count)
        hlavicka = False
        telo = False
        continue

    #ak sme zatial nematchli nic, tak sme vnutri tabulky
    res = re.match(r'^\s*\|', line)
    if res and telo:
        row = re.sub('\n','',line)
        rec.append(row)
        continue
    
    #dalsie riadky
    if record:
        record.parse_row(line)

f.close()
##################################################
#
#   vytvorenie grafov a vypis vysledkov
#
###################################################
print('###########################################')
print('Vysledky:')
print('UL_L1 = ' + str(int(ul_l1/8)) + ' B')
print('UL_L2 = ' + str(int(ul_l2/8)) + ' B')
print('\nUL peak: ' + str(ul_peak/(1024**2)) + ' MBps')
print('\nDL_L1 = ' + str(int(dl_l1/8)) + ' B')
print('DL_L2 = ' + str(int(dl_l2/8)) + ' B')

res = 0
for u in ul_l1_speed:
    res += u[1]
res = res / len(ul_l1_speed)
print('\nUL_L1_mean = ' + str(res) + ' kbps')
res = 0
for u in ul_mac_speed:
    res += u[1]
res = res/ len(ul_mac_speed)
print('UL_MAC_mean = ' + str(res) + ' kbps')
res = 0
for u in error_rate:
    res += u[1]
res = res/ len(error_rate)
print('\nError rate mean = ' + str(res*100)  + ' %')

print('TTI=2ms / TTI=10ms : ' + str(Table3.tti()))
print('\nNajdene bunky:')

for cell in cells:
    print('\nPSC : ' + str(cell))
    res = 0
    for v in ecno[cell]:
        res += v[1]
    res = res/ len(ecno[cell])
    print('Ec/No mean = ' + str(res) + ' dB')
    res = 0
    for u in rscp[cell]:
        res += u[1]
    res = res/ len(rscp[cell])
    print('RSCP mean = ' + str(res) + ' dB')
    
# + str(cell['primary_rssi']))

print('\nActive set:')
for k in active_set.keys():
    print(k)

print('\nMonitoring set:')
for k in monitoring_set.keys():
    print(k)

if max_tbs > 7110:
    device_EUL_category = 3
if max_tbs > 14484:
    device_EUL_category = 5
if max_tbs > 20000:
    device_EUL_category = 7

if (ul_peak > 0.73 * (1024**2)) and device_EUL_category <= 3:
    device_EUL_category = 3
if (ul_peak > 1.46 * (1024**2)) and device_EUL_category <= 5:
    device_EUL_category = 5
if (ul_peak > 2.0 * (1024**2)) and device_EUL_category <= 7:
    device_EUL_category = 7
print('\nDevice EUL category: ' + str(device_EUL_category))

print('\n#################################')
print('Bonus:')
#
print('Limit serving grantom: ' + str(limit_sg))
#
print('Limit obsahom buffra: ' + str(limit_buffer))
#znizovanie interferencie
print('Limit nedostatocnym vysielacim vykonom: ' + str(limit_power))
