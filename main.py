import argparse
import os
import logging.config
import requests
import sys
import pickle
from pandas import *
from datetime import datetime
from pprint import pprint


import config as conf


class Parser(object):

    @staticmethod
    def init_reports():
        for categorie in conf.categories_list:
            if not os.path.exists('front/' + categorie + '.html'):
                DataFrame().to_html('front/' + categorie + '.html', index=False)

    def __init__(self):
        logging.config.dictConfig(conf.dictLogConfig)
        # df = DataFrame(pandas.read_html('front/askstories.html')[0])
        # df.to_html('test.html', index=False)
        self.logger = logging.getLogger("DataParserApp")
        self.logger.info("Program started")
        self.argpars = argparse.ArgumentParser(description='Data parse.')
        self.argpars.add_argument('-c', action="store", dest="categories", nargs='+', default=conf.default_categories,
                            choices=conf.categories_list)
        self.args = self.argpars.parse_args()
        self.init_reports()

    def get_records_id(self):
        ids_records = {}
        for categorie in self.args.categories:
            self.logger.info("request was sent to obtain the list of IDs by category {}".format(categorie))
            request = requests.get(conf.categorie_url.format(categorie))
            self.logger.info("list is received")
            try:
                ids_records.update({categorie: request.json()})
            except requests.exceptions.RequestException as e:
                self.logger.error(e)
                print(e)
                sys.exit(1)
            print(len(ids_records), "ids received")
        with open("ids.pic", "wb") as f:
            all_ids = []
            for vals in ids_records.values():
                for val in vals:
                    all_ids.append(val)
            pickle.dump(all_ids, f)

        return ids_records

    def get_records(self):
        ids_records = self.get_records_id()
        self.logger.info("report generation started...")
        all_records = []
        with open('ids.pic', 'rb') as f:
            pickle_ids = pickle.load(f)
        for key, val in ids_records.items():
            for id_rec in val:
                try:
                    record_line = requests.get(conf.item_url.format(id_rec)).json()
                    record_line.update({'temp_type': key})
                except requests.exceptions.RequestException as e:
                    self.logger.error(e)
                    print(e)
                if record_line.get("score") >= conf.score:
                    date = datetime.date(datetime.fromtimestamp((record_line["time"])))
                    if date >= conf.from_date:
                        record_line["time"] = datetime.fromtimestamp((record_line["time"])).strftime(
                            "%Y-%m-%d-%H:%M:%S")
                        all_records.append(record_line)
                        self.logger.info("record {} added to result list".format(id_rec))
                        pprint(record_line)
                print(len(all_records), "records")
        return all_records


def prepare_report(*args):
    for arg in args:
        for arr in arg:
            arr.pop('temp_type')


def json_to_html(all_records):
    askstories, showstories, newstories, jobstories = [], [], [], []
    for record in all_records:
        if record.get('temp_type') == 'askstories':
            askstories.append(record)
        elif record.get('temp_type') == 'showstories':
            showstories.append(record)
        elif record.get('temp_type') == 'newstories':
            newstories.append(record)
        elif record.get('temp_type') == 'jobstories':
            jobstories.append(record)

    prepare_report(askstories, showstories, newstories, jobstories)
    askstories_rep = DataFrame(askstories)
    showstories_rep = DataFrame(showstories)
    newstories_rep = DataFrame(newstories)
    jobstories_rep = DataFrame(jobstories)

    askstories_rep.to_html('front/askstories.html', index=False)
    showstories_rep.to_html('front/showstories.html', index=False)
    newstories_rep.to_html('front/newstories.html', index=False)
    jobstories_rep.to_html('front/jobstories.html', index=False)


parser = Parser()
records = parser.get_records()
json_to_html(records)
