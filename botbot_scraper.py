""" Scrape logs from botbot pages. """
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from datetime import timedelta
from time import sleep
import argparse
import arrow
import json


help_description = """
BotBotParser is here to help parse channels listed on botbot.me.

defaults include:
    default start_date: 30 days ago
    default end_date: now
    default skip_info_lines: True (note: this skips name changes, quits/joins)

It uses the past day of freenode docker logs as --test

For more info: https://github.com/kjam/bot_scraper
"""


def get_browser():
    """ get a working browser, hopefully phantomjs!
        returns selenium webdriver instance
    """
    try:
        browser = webdriver.PhantomJS(
            desired_capabilities={
                'phantomjs.page.settings.resourceTimeout': '20'
            })
        browser.set_window_size(1120, 550)
    except WebDriverException:
        browser = webdriver.Firefox()
        browser.maximize()
        browser.set_timeout(20)
    return browser


def reload_page(network_name, chan_name, current_ts):
    """ If the page stops responding, reload it and attempt to get back to the
        same place.

        params:
            network_name: str
            chan_name: str
            current_ts: newest timestamp seen

        returns selenium webdriver
    """
    browser = get_browser()
    get_url(browser, network_name, chan_name, current_ts)
    return browser


def grab_all_messages(browser, message_cutoff=None,
                      skip_info_lines=True):
    """ Grab messages in the current browser session. i
        params: browser
        kwargs:
            message_cutoff (datetime of last saved msg - to avoid dupes)
            skip_info_lines (boolean)

        returns: list of log messages as a list of dicts
            dict keys:
                timestamp: str
                message: str
                nick: str
                datatype: str
    """
    logs = browser.find_elements_by_xpath('//ul[@id="Log"]/li')
    messages = []
    for log in logs:
        datatype = log.get_attribute('data-type')
        if skip_info_lines and datatype == 'info':
            continue
        nick = log.get_attribute('data-nick')
        timestamp = log.find_element_by_xpath(
            './/a/time').get_attribute('datetime')
        if message_cutoff and message_cutoff >= arrow.get(timestamp):
            continue
        message = log.find_element_by_xpath(
            './/div[contains(@class, "{}")]'.format(datatype)).text
        messages.append({
            'timestamp': timestamp,
            'message': message,
            'nick': nick,
            'datatype': datatype,
        })
    return messages


def get_timestamp(browser, ts_type='last'):
    """ Grab first or last timestamp on page for pagination choices.
        params:
            browser: selenium webdriver
        kwargs:
            ts_type: 'last' by default, 'first' for first timestamp
    returns Arrow datetime object
    """
    browser.implicitly_wait(3)
    logs = browser.find_elements_by_xpath('//ul[@id="Log"]/li')
    if ts_type == 'first':
        timestamp = logs[0].find_element_by_xpath(
            './/a/time').get_attribute('datetime')
    elif ts_type == 'last':
        timestamp = logs[-1].find_element_by_xpath(
            './/a/time').get_attribute('datetime')
    return arrow.get(timestamp)


def scroll_down(browser, current_ts):
    """ scroll down in the browser, with waits for lag.
        params:
            browser
            current_ts: datetime
    """
    tries = 0
    while get_timestamp(browser) <= current_ts and tries < 20:
        browser.execute_script("scrollBy(0, 450);")
        browser.implicitly_wait(4)
        sleep(2)
        tries += 1
    if tries == 20:
        raise WebDriverException


def get_url(browser, network_name, chan_name, start_date):
    """ get proper url for starting point
        params:
            browser: selenium webdriver
            network_name: str
            chan_name: str
            start_date: datetime
    """
    url = 'https://botbot.me/{}/{}/{}/'.format(network_name, chan_name,
                                               start_date.strftime('%Y-%m-%d'))
    browser.get(url)
    sleep(4)


def scrape_botbot_page(network_name, chan_name,
                       start_date=arrow.now() - timedelta(days=30),
                       end_date=arrow.now(),
                       output_file='',
                       skip_info_lines=True):
    """ Scrape any botbot page for any network you have http access to.
    params:
        network_name: str
        chan_name: str
    kwargs:
        start_date: datetime (default: 30 days ago)
        end_date: datetime (default: now)
        output_file: default (same directory json file:
            {network_name}_{chan_name}_{start_date}_{end_date}.json)
        skip_info_lines: default (True)
            note: this skips all the quit / join messages
    """
    browser = get_browser()
    all_messages = []

    get_url(browser, network_name, chan_name, start_date)
    current_end = get_timestamp(browser)
    msg_cutoff = start_date

    while current_end < end_date:
        print('current end: {}'.format(current_end))
        messages = grab_all_messages(browser, message_cutoff=msg_cutoff,
                                     skip_info_lines=skip_info_lines)
        if len(messages):
            msg_cutoff = arrow.get(messages[-1].get('timestamp'))
            all_messages.extend(messages)
        print('now at: {} messages'.format(len(all_messages)))
        print(all_messages[-2:])
        try:
            scroll_down(browser, current_end)
        except WebDriverException:
            browser.save_screenshot('error_{}.png'.format(
                arrow.now().strftime('%m%d%Y%H%M%S')))
            browser = reload_page(network_name, chan_name, current_end)
        current_end = get_timestamp(browser)

    if not output_file:
        output_file = 'chatlogs/{}_{}_{}_{}.json'.format(
            network_name, chan_name, start_date.strftime('%m%d%Y%H%M'),
            end_date.strftime('%m%d%Y%H%M'))
    json.dump(all_messages, open(output_file, 'w'))
    print('Scraping complete: check {}'.format(output_file))


def parse_datetime_args(datetime_string):
    """ Helper parser for command line datestrings.
        params:
            datetime_string: str (YYYY-MM-DD)
        returns arrow date object
    """
    try:
        return arrow.get(datetime_string, 'YYYY-MM-DD')
    except arrow.parser.ParserError:
        try:
            return arrow.get(datetime_string)
        except arrow.parser.ParserError:
            raise argparse.ArgumentTypeError(
                '{} is not proper datetime format: YYYY-MM-DD'.format(
                    datetime_string))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(help_description)
    parser.add_argument('--network_name', help="Network name (i.e. freenode)")
    parser.add_argument('--chan_name', help="Channel name (i.e. docker)")
    parser.add_argument('--start_date', help="Start DateTime or date string." +
                        " Most formats accepted, YYYY-MM-DD preferred. " +
                        "(default: 30 days ago)", type=parse_datetime_args)
    parser.add_argument('--end_date', help="End DateTime or date string. " +
                        "Most formats accepted, YYYY-MM-DD preferred. " +
                        "(default: now)", type=parse_datetime_args)
    parser.add_argument('--output_file', help="output file name " +
                        "(for now, JSON only)")
    parser.add_argument('--skip_info_lines',
                        help="skip quits, joins & namechanges. (default: true)",
                        action='store_true')
    parser.add_argument('--test', help="test using a day of docker chan data",
                        action='store_true')
    args = parser.parse_args()
    if args.test:
        scrape_botbot_page('freenode', 'docker',
                           start_date=arrow.now() - timedelta(days=1))

    elif not args.network_name or not args.chan_name:
        raise argparse.ArgumentTypeError("you must supply network / chan name")
    kwargs = dict((k, v) for k, v in vars(args).items()
                  if k in ['output_file', 'start_date', 'end_date',
                           'skip_info_lines'] and v is not None)
    scrape_botbot_page(args.network_name, args.chan_name, **kwargs)
