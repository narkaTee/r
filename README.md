R Project
===
This Splunk app provides a new Splunk search language
command 'r' that allows passing data from Splunk to the R-Engine
for calculation and then passing results back to Splunk for
further computation or visualization.

![Overview](https://raw.github.com/rfsp/r/master/private/screenshots/1_Overview.png)

R is a language and environment for statistical computing. It
provides a wide variety of statistical (linear and nonlinear
modeling, classical statistical tests, time-series analysis,
classification, clustering, ...) techniques, and is highly extensible.

Here's a link the actual [R-Project](http://www.r-project.org/) website.

Usage
---
The command requires one parameters which is either a actual R language
script:

![RforSplunk](http://i.imgur.com/VvXtf2j.png)


    | r "output = data.frame(Name=c('A','B','C'),Value=c(1,2,3))"

... or just the name of a R script file that is uploaded to the app:

    | r myscript.r

... here is another example:

     | r "
     gm_mean = function(x, na.rm=TRUE){
       exp(sum(log(x[x > 0]), na.rm=na.rm) / length(x))
     }
     data <- data.matrix(input);
     output <- apply(data, 2, gm_mean)"

Input comes in as `input` and you need to direct your results to `output` to get them back into Splunk.

Features
---
- Integration of a R script into the Splunk search pipeline
- Upload custom scripts (use the *source()* function to include them into the pipeline script)
- Manage external packages (use the *library()* function to load them from the pipeline script)
- Supports generating and streaming command mode
- Show R error messages on the Splunk UI
- Provide usage statitics of the app itself

Installation
---
This app is available on the [Splunk App Store](http://apps.splunk.com/app/1735/).
You can also clone the [repository](https://github.com/rfsp/r) to install the app manually.

Platforms
---
This app runs on a wide variety of Linux and Unix platforms, Windows and Mac OS X.

Contribute
---
Please send me your feedback, questions and suggestions
at [rfujara@splunk.com](rfujara@splunk.com).

You're also invited to clone/watch/star/fork the [GitHub project](https://github.com/rfsp/r),
send Pull Requests or just create Issues.
