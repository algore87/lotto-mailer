#!/usr/bin/env python3

from bs4 import BeautifulSoup
from requests import get
import re, sendgrid, os
from sendgrid.helpers.mail import *
import datetime
datetime.datetime.timetz
"""
TODO: sendgrid webhook to receive data from recipient (get superzahl)
TODO: add mLab MongoDB (Heroku Add-on) to track results
TODO: add html/css to make the output mail look pretty
"""
dev_mode = True

my_numbers = [  [3, 12, 17, 26, 30, 41],
                [2, 3, 7, 10, 28, 37],
                [1, 5, 7, 12, 14, 20],
                [18, 19, 20, 25, 31, 38],
                [4, 12, 17, 25, 33, 37],
                [11, 17, 29, 33, 46, 49]]
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
key = get_file_contents("sendgrid_api_key")
if key != None:
    os.environ['SENDGRID_API_KEY'] = key

# parser stuff
lotto_url = "https://www.lotto.de/lotto-6aus49/lottozahlen"
response = get(lotto_url)
response.encoding = "utf-8"

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
lotto_dict = {"date": "", "numbers":[]}
lotto_dict["date"] = lotto_date_soup.text
for item in lotto_winning_numbers_soup:
    lotto_dict["numbers"].append(int(item.text))
lotto_dict["super_nr"] = lotto_dict["numbers"].pop()

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
    output_str += lotto_dict["date"] + "\n" \
    + "Gewinnzahlen: " + str(lotto_dict["numbers"]) + " SZ: " + str(lotto_dict["super_nr"]) + "\n" \
    + "Eigene Zahlen + Treffer: " + "\n"
    win_without_sz = 0.0
    win_with_sz = 0.0
    for numbers in my_numbers:
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


def get_html_output_str():
    output_str = welcome_msg + "<br><br>"
    output_str += "<u>" + lotto_dict["date"] + "</u><br>" \
    + "Gewinnzahlen: " + "<b>" + str(lotto_dict["numbers"])[1:-1] + "</b>" + " SZ: " + str(lotto_dict["super_nr"]) + "<br><br>" \
    + "<u>Ergebnis mit ggf. <i>Gewinn (ohne, mit SZ)</i></u>: " + "<br>"
    win_without_sz = 0.0
    win_with_sz = 0.0
    for numbers in my_numbers:
        hit_set = set(numbers) & set(lotto_dict["numbers"])
        for i in range(len(numbers)):
            if numbers[i] in lotto_dict["numbers"]:
                numbers[i] = "<b>" + str(numbers[i]) + "</b>"
        output_str += str(numbers)[1:-1].replace("'","")
        hits = len(hit_set)
        if hits:
            quote_tuple = get_quote_with_hit(hits)
            win_without_sz += quote_tuple[0]
            win_with_sz += quote_tuple[1]
            output_str += " ---> " + str(hits) + " Treffer"
            if hits >= 2 and has_quote:
                output_str += ": <i>{:.2f} €, {:.2f} €</i>".format(*quote_tuple)
        output_str += "<br>"
    if has_quote:
        output_str += "<br><u>Gesamtgewinn (ohne, mit SZ)</u>: <b>{:.2f} €</b>, <b>{:.2f} €</b><br>".format(win_without_sz, win_with_sz)
    else:
        output_str += "<br>noch keine Quote vorhanden.<br>"
    output_str += "<i>" + no_warranty_msg + "</i><br><br>" + bye_msg + "<br>" + name_msg
    return output_str
if dev_mode:
    print(get_html_output_str())


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
    to_mail_list = ["alexschott87@gmail.com", 
                    "scotty0655@gmail.com"]

def mailto(recipients):
    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("alexschott87@gmail.com")
    subject = "Lottozahlen: " + lotto_dict["date"]
    content = Content("text/html", get_html_output_str())
    for recipient in recipients: # mail to all recipients
        mail = Mail(from_email, subject, Email(recipient), content)
        response = sg.client.mail.send.post(request_body=mail.get())
        print(response.status_code)
        print(response.body)
        print(response.headers)

if runOnSchedule() or dev_mode:
    #print("Your API key is: {}".format(os.environ.get('SENDGRID_API_KEY')))
    mailto(to_mail_list)

