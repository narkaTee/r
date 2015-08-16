# R Project

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

## Usage

The command requires one parameters which is either a actual R language
script:

![RforSplunk](http://i.imgur.com/VvXtf2j.png)

## Examples


1. Output a table with column names to Splunk

    ````
    | r "output = data.frame(Name=c('A','B','C'),Value=c(1,2,3))"
    ````

2. Run a search, and have R output the column names available in the input

    ````
    index=_internal earliest=-15m
    |r "output=colnames(input)"
    ````

    Input from Splunk comes in as `input` and you need to direct your results to
    `output` to get them back into Splunk.

3. Calculate the total incoming log volume using a search on the _internal index, and have R sum the "kb" field.

    ````
    index=_internal sourcetype=splunkd component=Metrics group=per_sourcetype_thruput earliest=-1h
    |r "output=sum(input$kb)"
    ````

4. Do the same, but have R group by incoming sourcetype (available through the "series" field)

    ````
    index=_internal sourcetype=splunkd component=Metrics group=per_sourcetype_thruput earliest=-1h
    |r "output=aggregate(input$kb, by=list(input$series), FUN=sum)"
    ````

5. Run an R script

    Just run an R script file that is uploaded to the app:

    ````
    | r myscript.r
    ````

6. Calculate geometric mean from matrix column values

    First create this matrix:

    |   |   |    |
    |---|---|----|
    | 1 | 2 | 4  |
    | 2 | 8 | 16 |

    with these Splunk statements:

    ````
    |stats count as a |eval a=1 |eval b=2 |eval c=4
    |append [ |stats count as a |eval a=2 |eval b=8 | eval c=16 ]
    ````

    and calculate the geometric mean of the column values. If you want to calculate
    the geometric mean of the rows, change 2 -> 1 in the apply() function

    ````
    | r "
         gm_mean = function(x, na.rm=TRUE){
           exp(sum(log(x[x > 0]), na.rm=na.rm) / length(x))
         }
         data <- data.matrix(input);
         output <- apply(data, 2, gm_mean)
        "
    ````


7. Determine sunspot periodicity using FFT

    This can be done with a publicly available dataset that lists the sunspot activity from the year 1700 until now. The sunspots.csv file is included in the app to play with.

    | Year | Sunspots |
    |------|----------|
    | 1700 | 5
    | 1701 | 11
    | ...  | ...
    
    To apply FFT on this data, it needs to be detrended. This is done by calculating the difference in sunspots with the previous year. Enter streamstats. Then the fft() function is then applied to the Sunspots column, and the frequencies are converted back to cycles 

    ````
    | inputlookup sunspots.csv
    | streamstats current=f last(Sunspots) as new window=2
    | eval Sunspots=Sunspots-new |fields - new
    | search Sunspots=* 
    | r output="transform(input,Power=(4/308)*(abs(fft(input$Sunspots))^2)[1:154],Freq=(0:153)/308)"
    | eval Power=if(Freq==0,0,Power)
    | eval Period=1/Freq
    | sort Period
    | table Period,Power
    ````

    or replace the streamstats contraption above with the R diff() function. Since this is an example, please ignore the ineffiency of using multiple R pipelines.

    ````
    | inputlookup sunspots.csv
    | r output="diff(input$Sunspots)"
    | rename x as Sunspots
    | r output="transform(input,Power=(4/308)*(abs(fft(input$Sunspots))^2)[1:154],Freq=(0:153)/308)"
    | eval Power=if(Freq==0,0,Power)
    | eval Period=1/Freq
    | sort Period
    | table Period,Power
    ````

    This all leads to a chart with a huge spike around the 11 year period, indicating sunspots occur in a cycle with a length of around 11 years.

## Features

- Integration of a R script into the Splunk search pipeline
- Upload custom scripts (use the *source()* function to include them into the pipeline script)
- Manage external packages (use the *library()* function to load them from the pipeline script)
- Supports generating and streaming command mode
- Show R error messages on the Splunk UI
- Provide usage statitics of the app itself

## Installation

This app is available on the [Splunk App Store](http://apps.splunk.com/app/1735/).
You can also clone the [repository](https://github.com/rfsp/r) to install the app manually.

## Platforms

This app runs on a wide variety of Linux and Unix platforms, Windows and Mac OS X.

## Contribute

Please send me your feedback, questions and suggestions
at [rfujara@splunk.com](rfujara@splunk.com).

You're also invited to clone/watch/star/fork the [GitHub project](https://github.com/rfsp/r),
send Pull Requests or just create Issues.
