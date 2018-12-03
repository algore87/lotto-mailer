#!/usr/bin/env python3

from bs4 import BeautifulSoup
from requests import get
import re, sendgrid, os
from sendgrid.helpers.mail import *
import datetime
datetime.datetime.timetz
from pymongo import MongoClient # mongodb
"""
TODO: add super_nr as argument and change output (only if SZ hit with Treffer{},{} + SZ)
TODO: clean up code
TODO: sendgrid webhook to receive data from recipient (get superzahl)
TODO: add mLab MongoDB (Heroku Add-on) to track results
TODO: add html/css to make the output mail look pretty

Zusätzliche Spezifikationen:
Allgemeines:
-> Imports evtl. From Datetime Import Datetime # um datetime.datetime zu fixen

Programm:
-> Füge Superzahl als Argument hinzu
    - python lotto_mailer.py 8 # setzt Superzahl auf 8 usage: ./python_mailer <sz>
    - superzahl nur zwischen [0-9]
    - argument hat priorität

Datenbank:
-> Change lotto_quotes collection
    - add [day: "Mittwoch | Samstag"] # damit nach Mittwoch / Samstage sortiert werden kann
    - add [win: 73.00] # um den Gewinn zu verfolgen (Gewinn mit / ohne SZ)
    - add [pot: 2948591.55] # Pot Gesamt-Preis

Ausgabe:
-> Separation of Concerns
    - Output sollte nur Output sein, evtl. mit Polymorphie, für Console / Mail je unterschiedlicher Aufruf
    - D.h. auch Berechnung und Ergebnisse vom Output trennen.
    Ideen:
        - Evtl. Ohne Sz / Sz entfernen, wenn SZ bei daddy fix 7 ist
        - Oder Ohne Sz / Sz drin lassen, aber das getroffene FETT

Heroku Scheduler:
-> Führe Skript Mi, Fr, Sa, Mo aus
    - Mi für neueste Lottozahlen in Datenbank am Mittwoch
    - Fr für Quoten vom Mittwoch
    - Sa für neueste Lottozahlen in Datenbank am Samstag
    - Mo für Quoten vom Samstag
"""

dev_mode = False or int(os.environ.get('DEBUG')) # change debug state in heroku itself

my_numbers = [  [3, 12, 17, 26, 30, 41],
                [2, 3, 7, 10, 28, 37],
                [1, 5, 7, 12, 14, 20],
                [18, 19, 20, 25, 31, 38],
                [4, 12, 17, 25, 33, 37],
                [11, 17, 29, 33, 46, 49]]
my_super_nr = 7
"""
my_numbers = [  [4, 9, 17, 26, 30, 41],
                [2, 3, 7, 10, 22, 27],
                [4, 9, 22, 23, 27, 32],
                [18, 19, 20, 25, 31, 38],
                [4, 12, 17, 25, 33, 37],
                [4, 9, 22, 27, 31, 41]]
"""
def get_file_contents(filename):
    """ Given a filename,
        return the contents of that file
    """
    try:
        with open(filename, 'r') as f:
            # It's assumed our file contains a single line,
            # with our API key
            return f.read().strip()
    except FileNotFoundError:
        print("'{}' file not found".format(filename))
### Initialisation   
# Mongo DB
db_user_colon_pw = get_file_contents("heroku_mlab_mongodb")
if db_user_colon_pw != None:
    os.environ['MLAB_MONGO_LOGIN'] = db_user_colon_pw
else:
    db_user_colon_pw = os.environ.get('MLAB_MONGO_LOGIN')
db_name = 'heroku_l8nz6hj9'
client = MongoClient('mongodb://' + db_user_colon_pw + '@ds211504.mlab.com:11504/' + db_name)
db = client[db_name] # db

# Sendgrid
key = get_file_contents("sendgrid_api_key")
if key != None:
    os.environ['SENDGRID_API_KEY'] = key


# parser stuff
lotto_url = "https://www.lotto.de/lotto-6aus49/lottozahlen"
response = get(lotto_url)
response.encoding = "utf-8"

def get_date(s):
    """
    Ziehung vom Mittwoch, 01.01.2018... -> str("01.01.2018")
    """
    reobj = re.search('[0-9]{2}.[0-9]{2}.[0-9]{4}',s)
    if reobj != None:
        return reobj.group(0)
    else:
        return None

def get_day_str_from_date_str(s):
    """
    01.01.2018 -> 0-6 -> "Montag | Dienstag | Mittwoch | Donnerstag | Freitag | Samstag | Sonntag
    """
    pass

def string_to_float(s):
    """
    Spieleinsatz: 20.686.254,00 € -> float(20686254.00)
    """
    s = re.sub('[^0-9,]', '', s)
    s = s.replace(',', '.')
    try:
        f = float(s)
    except ValueError:
        return 0.00
    else:
        return f

"""
Parse Html
"""
lotto_soup = BeautifulSoup(response.text, 'html.parser')
lotto_6_49_soup = lotto_soup.find('div', class_="WinningNumbers WinningNumbers--lotto6aus49")
lotto_winning_numbers_soup = lotto_6_49_soup.find_all('span', class_="LottoBall__circle")
lotto_date_soup = lotto_soup.find('span', class_="WinningNumbers__date")
lotto_6_49_quotes_soup = lotto_soup.find('div', class_= "OddsTableContainer__content")
lotto_6_49_quote_table_entries_soup = lotto_soup.find_all('tr', class_="OddsTableRow") # you need to discard last item

"""
Winning Numbers
"""
lotto_dict = {"numbers": []} # {"date": "21.11.2018", "numbers":[18, 24, 29, 30, 42, 47], "super_nr": 7}
date = get_date(lotto_date_soup.text)
if date:
    lotto_dict["_id"] = datetime.datetime.strptime(date, "%d.%m.%Y")
    lotto_dict["date"] = date
    for item in lotto_winning_numbers_soup:
        lotto_dict["numbers"].append(int(item.text))
    lotto_dict["super_nr"] = lotto_dict["numbers"].pop()
else:
    raise ValueError

try:
    db.lotto_numbers.insert_one(lotto_dict)
except Exception as e:
    print(e)


"""
Quotes
"""
quotes_list = []
has_quote = True
game_amount = lotto_6_49_quotes_soup.find('div', class_="GameAmount").text
if game_amount == "Spieleinsatz: wird ermittelt": # no quote
    # game_amount = string_to_float(game_amount)
    has_quote = False
else: # get quote
    for row in range(1, 10):
        table_entries = lotto_6_49_quote_table_entries_soup[row].find_all('td')
        quote_dict = {}
        quote_dict["Klasse"] = int(table_entries[0].text)
        quote_dict["Anzahl Richtige"] = table_entries[1].text
        quote_dict["Gewinne"] = int(table_entries[2].text[:-2].replace('.',''))
        quote_dict["Quoten"] = string_to_float(table_entries[3].text)
        quotes_list.append(quote_dict)
    
    lotto_quote = {}
    lotto_quote["_id"] = datetime.datetime.strptime(date, "%d.%m.%Y")
    lotto_quote["date"] = date
    lotto_quote["quotes_list"] = quotes_list
    try:
        db.lotto_quotes.insert_one(lotto_quote)
    except Exception as e:
        print(e)

def get_quote_with_hit(hit): # hit: Str(nr) or Str("nrSZ")
    quote_with_sz = 0.0
    quote_without_sz = 0.0
    for quote in quotes_list:
        if quote["Anzahl Richtige"].startswith(str(hit)) and \
        quote["Anzahl Richtige"].endswith("SZ"):
            quote_with_sz = quote["Quoten"]
        elif quote["Anzahl Richtige"].startswith(str(hit)):
            quote_without_sz = quote["Quoten"]
    return (quote_without_sz, quote_with_sz)

# overall money pot

#print(game_amount)


"""
Output
"""
welcome_msg = "Hi Paps, im Anhang deine Lottoergebnisse."
no_warranty_msg = "Alle Angaben ohne Gewähr."
bye_msg = "Viele Grüße"
name_msg = "Alexander Schott"

def linebreak_adder_from_plain_to_html(s):
    s = s.replace('\n', "<br>")
    return s

def get_plain_output_str():
    output_str = ""
    output_str += lotto_date_soup.text + "\n" \
    + "Gewinnzahlen: " + str(lotto_dict["numbers"]) + " SZ: " + str(lotto_dict["super_nr"]) + "\n" \
    + "Eigene Zahlen + Treffer: " + "\n"
    win_without_sz = 0.0
    win_with_sz = 0.0
    for numbers in my_numbers.copy():
        output_str += str(numbers)
        hit_set = set(numbers) & set(lotto_dict["numbers"])
        hits = len(hit_set)
        if hits:
            quote_tuple = get_quote_with_hit(hits)
            win_without_sz += quote_tuple[0]
            win_with_sz += quote_tuple[1]
            output_str += " Treffer: " + str(hit_set)
            if hits >= 2 and has_quote:
                output_str += " Gewinn (ohne,mit SZ): {:.2f} €, {:.2f} €".format(*quote_tuple)
        output_str += "\n"
    if has_quote:
        output_str += "Gesamtgewinn (ohne, mit SZ): {:.2f} €, {:.2f} €".format(win_without_sz, win_with_sz)
    else:
        output_str += "Noch keine Quote vorhanden"
    return output_str
print(get_plain_output_str())


def get_html_output_str(): # BUG
    output_str = welcome_msg + "<br><br>"
    output_str += "<u>" + lotto_date_soup.text + "</u><br>" \
    + "Gewinnzahlen: " + "<b>" + str(lotto_dict["numbers"])[1:-1] + "</b>" + " SZ: " 
    if my_super_nr == lotto_dict["super_nr"]:
        output_str += "<b>" + str(lotto_dict["super_nr"]) + "</b>"
    else:
        output_str += str(lotto_dict["super_nr"])
    output_str += "<br><br>" \
    + "<u>Ergebnis mit ggf. <i>Gewinn</i></u>: " + "<br>"
    win_without_sz = 0.0
    win_with_sz = 0.0
    for numbers in my_numbers: # BUG: Numbers changes even if my_numbers.copy() [[]<-- referenziert,[]]
        hit_set = set(numbers) & set(lotto_dict["numbers"])
        #print(numbers)
        #print(hit_set)
        for i in range(len(numbers)):
            if numbers[i] in lotto_dict["numbers"]:
                numbers[i] = "<b>" + str(numbers[i]) + "</b>" # changes my_numbers[[numbers*][][]]
        output_str += str(numbers)[1:-1].replace("'","")
        hits = len(hit_set)
        if hits:
            quote_tuple = get_quote_with_hit(hits)
            win_without_sz += quote_tuple[0]
            win_with_sz += quote_tuple[1]
            output_str += " ---> " + str(hits) + " Treffer"
            if my_super_nr == lotto_dict["super_nr"]:
                output_str += " + SZ"
            if hits >= 2 and has_quote:
                output_str += ": <i>"
                if my_super_nr == lotto_dict["super_nr"]:
                    output_str += "{:.2f} €</i>".format(quote_tuple[1])
                else:
                    output_str += "{:.2f} €</i>".format(quote_tuple[0])
        output_str += "<br>"
    if has_quote:
        output_str += "<br><u>Gesamtgewinn</u>: <b>"
        if my_super_nr == lotto_dict["super_nr"]:
            output_str += "{:.2f} €</b><br>".format(win_with_sz)
        else:
            output_str += "{:.2f} €</b><br>".format(win_without_sz)
    else:
        output_str += "<br>noch keine Quote vorhanden.<br>"
    output_str += "<i>" + no_warranty_msg + "</i><br><br>" + bye_msg + "<br>" + name_msg
    return output_str
html_output_str = get_html_output_str() # BUG: second get_html_output_str() doesn't show hits (cause numbers changed!)
if dev_mode:
    print(html_output_str)


print(datetime.datetime.utcnow())
print("Weekday: {}\nUTC Hour: {}".format(datetime.date.today().isoweekday(), datetime.datetime.utcnow().hour))
def runOnSchedule():
    if datetime.date.today().isoweekday() == 1  \
    and datetime.datetime.utcnow().hour == 9: # run only on monday between 9 and 10 am utc
        return True
    else:
        return False
        
# sendgrid stuff
if dev_mode:
    to_mail_list = ["alexschott87@gmail.com"]
else:
    to_mail_list = ["scotty0655@gmail.com"]

def mailto(recipients):
    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("alexschott87@gmail.com")
    subject = "Lottozahlen: " + lotto_date_soup.text
    content = Content("text/html", html_output_str)
    for recipient in recipients: # mail to all recipients
        mail = Mail(from_email, subject, Email(recipient), content)
        response = sg.client.mail.send.post(request_body=mail.get())
        print(response.status_code)
        print(response.body)
        print(response.headers)

if runOnSchedule() or dev_mode:
    #print("Your API key is: {}".format(os.environ.get('SENDGRID_API_KEY')))
    mailto(to_mail_list)

