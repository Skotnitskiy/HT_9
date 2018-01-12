import argparse
import os
import logging.config
import requests
import sys
import shutil
from pandas import *
from datetime import datetime
from pprint import pprint


import config as conf


class Parser(object):
    def __init__(self):
        logging.config.dictConfig(conf.dictLogConfig)
        self.logger = logging.getLogger("DataParserApp")
        self.logger.info("Program started")
        self.argpars = argparse.ArgumentParser(description='Data parse.')
        self.argpars.add_argument('-c', action="store", dest="categories", nargs='+', default=conf.default_categories,
                            choices=conf.categories_list)
        self.args = self.argpars.parse_args()
        # create dir
        if not os.path.exists(conf.results_path):
            os.mkdir(conf.results_path)
            self.logger.info("results dir created")
        else:
            self.logger.info("results directory already exists")

    def get_records(self):
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

        all_records = []
        self.logger.info("report generation started...")
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


def generate_report():
    shutil.copytree("front/", conf.results_path + "/report")


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

    askstories_rep.to_html('front/askstories.html')
    showstories_rep.to_html('front/showstories.html')
    newstories_rep.to_html('front/newstories.html')
    jobstories_rep.to_html('front/jobstories.html')


parser = Parser()
records = parser.get_records()
# generate_report()
json_to_html(records)
