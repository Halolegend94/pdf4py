# pdf4py

A PDF parser written in Python 3 with no external dependencies.


## Standard coverage

You can check how many features of the standard are implemented and what is the progress on supporting the missing ones by checking the standard coverage [page](StandardCoverage.md).


## TODO list

- To support streams whose bytes are defined into an external file. I still have to understand in which way this file is specified. Waiting for an example to show up.
- To implement a caching system not to read objects from file every time they are required.