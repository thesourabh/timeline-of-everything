# Timeline of Everything

Timeline of Everything allows you to create timelines and compare them with other ones to potentially find interesting new things.

## Installation

To set it up, you need [Python 3](https://www.python.org/download/releases/3.0/).

Once Python is in your environment variables, verify you have it by running:

```sh
$ python -V
```

Next, install the dependencies by running:

```sh
$ pip install -r requirements.txt
```

If you have a Windows system, I have written two helper .bat files that will run the next commands for you.

  - runAndReset.bat : Reset the database and run the app (always do this for the first time or when there's an error in the database)
  - run.bat: Run without resetting the database (use this when you have already added events or timelines that you don't want to lose)