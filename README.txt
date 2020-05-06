This is the assignment repo for COSC364-Assignment 1

Comment Syntax:
There are 4 types of comments used:
"""These are docstrings. They currently only occur as function descriptions"""
#Comments to describe functionality, and hopefully make it easier to follow
## UNSURE are comments expressing uncertaintly about how to implement something correctly
### TODO comments mark functinality that has yet to be implemented


Config File Syntax:
Each line represents a required parameter. Ordering doesn't matter, but there must be
on space after each parameter, and each value for that parameter. E.g:
"router-id 1"
"input-ports 5207 6201 7345"
"outputs 5000-1-1 5002-5-4"
"//Comments have been marked like this. They will be ignored by the config function"



Notes: 
30/4 - None of the protocol has been implemented yet. I've mostly just done the config file.
       It's functional for the most part, but still has some unfinished elements
6/5 - Unsure how to go about dealing with the sockets.