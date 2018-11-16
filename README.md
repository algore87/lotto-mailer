[![HitCount](http://hits.dwyl.io/algore87/lotto-mailer.svg)](http://hits.dwyl.io/algore87/lotto-mailer)

# Lotto-Mailer
> lotto results send per mail via sendgrid and deployed with heroku

This python script is used to learn how to parse html with `beautifulsoup`, extract the informations needed, turn them into something useful and make use of the `sendgrid api` to send it via email. The example parses the current lotto results, compares them to a list of numbers given and prints out the quotes (money) you would win.

## Prerequisites
* [requests](http://docs.python-requests.org/en/master/) - send organic grass-fed HTTP/1.1 requests
* [urllib3](https://github.com/urllib3/urllib3) - http client *(requests dependancy)*
* [beautifulsoup](https://www.crummy.com/software/BeautifulSoup/) - Screen scraper used for parsing html
* [sendgrid](https://sendgrid.com/) - :email: email delivery API

```shell
pip install -r requirements.txt
```
Install every library listed above with the python packetmanager pip.

### Initial Configuration (local)
1) Create a [sendgrid](https://app.sendgrid.com/settings/api_keys) account and get an API key
2) Create a :page_facing_up: called `sendgrid_api_key` with `echo "<<your API Key>>" > sendgrid_api_key`
3) Change `my_numbers` in `lotto_mailer.py` to match your lotto numbers
4) Change `welcome_msg`, `bye_msg`, `name_msg` to match your text sent by mail
5) Change variables `from_email` and `to_email` to match mail adresses

### Running (local)

```shell
python3 lotto_mailer.py
```
Start the script, prints out to console and start sending information via mail.

## Deploying

We use [Heroku](https://www.heroku.com/) to deploy and manage our app as simple and fast as possible by linking our github repo with heroku.

### Heroku Files
* :page_facing_up: `runtime.txt` - to specify python build version
* :page_facing_up: `Procfile` - worker dyno *(to run the script)*
### Heroku Add-ons
* [Heroku Scheduler](https://elements.heroku.com/addons/scheduler) - run jobs on your app at scheduled time intervals *(cron like tool)*

### Quick Todo
1) Create new app *(app-name, choose a region --> Create app)*
2) Deploy -- Deployment method -- *(select GitHub)* -- Connect to GitHub -- *(select your repo --> Search, --> Connect)* -- Manual deploy *(Enter the name of the branch --> Deploy Branch)*
3) Settings -- Config Vars *(--> Reveal Config Vars, add `SENDGRID_API_KEY`  - `<<your API Key>>`)*
4) Resources -- Free Dynos *(--> Edit --> shift the switch to right --> Confirm)*

After that your script should execute and your mail will be send.

## Features

* Scheduled running of the script with [Heroku Scheduler](https://elements.heroku.com/addons/scheduler)
* Extended functionality with bash command to enhance scheduling ability

## Configuration

Setup the Heroku Scheduler to match your scheduling needs. By default you can only run your script every 10 minutes, every hour or every day.

Example:
```shell
if [ "$(date +%u)" = 1 ]; then python lotto_mailer.py; fi # will execute every monday
```
Change your scheduling: Resources -- Add-ons -- Heroku Scheduler --> Add new job. The code above combined with `Daily` FREQUENCY and NEXT DUE `09:00` UTC will get executed every week on monday at 9 am. *For further information check :file_folder: usefull stuff*

#### Issues
The python command can't get executed by the scheduler.
#### Solution
Add `PYTHONPATH` - `/app/.heroku/python` to your Config Vars in Settings.


## What's next?

* clean up code
* make it more efficient
* add html and css to send really nice looking mails


## License

The MIT License (MIT)

Copyright (c) 2017 Alexander Schott

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
