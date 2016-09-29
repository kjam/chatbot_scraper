Bot Scraper
=========================

A simple scraper for public IRC / other chat-like things. Right now it only supports BotBot but please send along suggestions / contributions for extending!

Scripts
--------

 * `botbot_scraper.py` - A script to simply scrape flights from [botbot.me](http://botbot.me)

Requirements
------------

Install the necessary requirements using the `requirements.txt` file. Not all scripts need all requirements, so please check the script you are interested in using if you'd like to individually install and use the packages. It is only tested with Python3, but it should be Python2 compatible with a few minor changes.


FAQ
-------

- Why is it slow?

Could it be faster? Yes! Would then it be pretty spammy and potentially break / get blocked. Yes! Can I modify it to make it faster? Be my guest! If it's a performance improvement rather than removing waits and sleeps, send along!

- How far back can it go?

So far, I have only tried one week of data at a time (due to time constraints). This could also be run concurrently using the start and end dates, meaning it might be best to just grab 3-7 days at a time with a series of workers rather than grab 100 days from one sad scraper... wah wahhhhh... Please keep in mind to not be evil, and only run a few concurrently at once. :)


TO DO (feel free to help / chime in!)
-----
 * Parse datetime, not just date
 * Find more bot pages
 * CSV output support
 * Integrate with an actual logger bot? (launch bot: can haz logs?)
 * Add public slack parsing? 

Questions?
----------
/msg kjam on twitter or freenode.

