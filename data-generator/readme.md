Building a proof-of-concept script for composing the time-series data. The thought is to have one set of tools for creating data sets that can be replayed, and another for generating a live data feed. 

With data set files, we will be able to curate datasets with anomaly artifacts that complements the story that drove the data design.  

Started with a script that generates and writes data set files. Now refactoring to generate a real-time time-series, using the same "data with anomalies" design, but instead posting the data to the Events API. 
