Splunk R App
===
R is a free software environment for statistical computing.
Here's a link the [R-Project](http://www.r-project.org/) website.

This app provides a Splunk search language command *r* that allows passing
data from Splunk to R and then passing results back to Splunk.

    | sampleproductorders | r "events=summary(events)"

Status
---
This project is in a very early alpha status and should not be used in a
production environment.

Installation
---
Will be available on apps.splunk.com ...