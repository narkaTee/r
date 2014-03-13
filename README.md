R - Statistical Computing
===
This Splunk app provides a new Splunk search language
command 'r' that allows passing data from Splunk to the R-Engine
for calculation and then passing results back to Splunk for
further computation or visualization.

![Overview](https://raw.github.com/rfsp/r/master/django/r/static/r/overview.png)

R is a language and environment for statistical computing. It
provides a wide variety of statistical (linear and nonlinear
modeling, classical statistical tests, time-series analysis,
classification, clustering, ...) techniques, and is highly extensible.

Here's a link the actual [R-Project](http://www.r-project.org/) website.

Usage
---
The command required at least one parameters. The actual R language script.
A minimal command syntax looks like this:

    | r "<R script>"

... for example:

    | r "output = data.frame(Name=c('A','B','C'),Value=c(1,2,3))"

TODO: implement additional parameters

Status
---
This project is in a very early alpha status and should not be used in a
production environment.

Contribute
---
I'm not a R expert, that's why I need your help
to show more and better examples (see below).

Please send me your feedback, questions and suggestions
at [rfujara@splunk.com](rfujara@splunk.com).

You're also invited to clone/watch/star/fork the [GitHub project](https://github.com/rfsp/r),
send Pull Requests or just create Issues.

Features
---
- ...
- Manage Custom Scripts (use the *source()* function to include them)
- TODO

Installation
---
This app is available on the [Splunk App Store](http://apps.splunk.com/app/1735/)

Or you can clone this repository to install the app manually.

Platforms
---
Currently only Mac OS X and Windows are supported.
Linux and Unix will be supported in future.
