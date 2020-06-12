# spreadsheets_microservice.py [![CircleCI](https://badgen.net/circleci/github/SFDigitalServices/spreadsheets_microservice/master)](https://circleci.com/gh/SFDigitalServices/spreadsheets_microservice) [![Coverage Status](https://coveralls.io/repos/github/SFDigitalServices/spreadsheets_microservice/badge.svg?branch=master)](https://coveralls.io/github/SFDigitalServices/spreadsheets_microservice?branch=master)
Microservice for interacting with online spreadsheets

## Get started

Install Pipenv (if needed)
> $ pip install --user pipenv

Install included packages
> $ pipenv install --dev

Set ACCESS_KEY environment var and start WSGI Server
> $ ACCESS_KEY=123456 pipenv run gunicorn 'service.microservice:start_service()'

Run Pytest
> $ pipenv run python -m pytest

Get code coverage report
> $ pipenv run python -m pytest --cov=service tests/ --cov-fail-under=100

Open with cURL or web browser
> $ curl --header "ACCESS_KEY: 123456" http://127.0.0.1:8000/welcome

## Development 
Auto-reload on code changes
> $ pipenv run gunicorn --reload 'service.microservice:start_service()'

Code coverage command with missing statement line numbers  
> $ pipenv run python -m pytest --cov=service tests/ --cov-report term-missing

Set up git hook scripts with pre-commit
> $ pipenv run pre-commit install

## Setting up Google Sheet sharing
[Instructions] (https://towardsdatascience.com/accessing-google-spreadsheet-data-using-python-90a5bc214fd2) for creating a service account 

## Continuous integration
* CircleCI builds fail when trying to run coveralls.
    1. Log into coveralls.io to obtain the coverall token for your repo.
    2. Create an environment variable in CircleCI with the name COVERALLS_REPO_TOKEN and the coverall token value.

## Heroku Integration
* Set ACCESS_TOKEN environment variable and pass it as a header in requests
