# Close Calls Philly

## Team Members
* Katie Jiang
* Daniel Zhang
* Natasha Narang
* Sanjay Subramanian

## Setting up for Python 3

#####  Clone the repo

```
$ git clone https://github.com/hack4impact/close-calls-philly.git
$ cd vision-zero-philly
```

##### Initialize a virtualenv

```
$ pip install virtualenv
$ virtualenv -p python3 env
$ source env/bin/activate
```

##### Install the app dependencies

```
$ pip install -r requirements.txt
```

##### Other dependencies for running locally

You need to install [Foreman](https://ddollar.github.io/foreman/) and [Redis](http://redis.io/). Chances are, these commands will work:

```
$ gem install foreman
```

Mac (using [homebrew](http://brew.sh/)):

```
$ brew install redis
```

Linux:

```
$ sudo apt-get install redis-server
```


##### Create the database

```
$ python manage.py recreate_db
```

##### Other setup (initialize database)

```
$ python manage.py setup_dev
```

##### [Optional] Add fake data to the database

```
$ python manage.py add_fake_data
```

##### [Optional] Import some actual data

```
$ python manage.py parse_csv -f poll244.csv
```

## Running the app

```
$ source env/bin/activate
$ honcho start -f Local
```

## License
[MIT License](LICENSE.md)
