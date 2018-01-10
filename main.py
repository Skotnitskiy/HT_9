import argparse
import csv
import os
import logging.config
import requests
import sys

from datetime import datetime
from pprint import pprint

import config as conf

logging.config.dictConfig(conf.dictLogConfig)
logger = logging.getLogger("DataParserApp")
logger.info("Program started")

parser = argparse.ArgumentParser(description='Data parse.')
parser.add_argument('-c', action="store", dest="categorie", default=conf.default_categorie,
                    choices=conf.categories_list)
args = parser.parse_args()
# create dir
if not os.path.exists(conf.results_path):
    os.mkdir(conf.results_path)
    logger.info("results dir created")
else:
    logger.info("results directory already exists")

logger.info("request was sent to obtain the list of IDs by category {}".format(args.categorie))
request = requests.get(conf.categorie_url.format(args.categorie))
logger.info("list is received")
try:
    ids_records = request.json()
except requests.exceptions.RequestException as e:
    logger.error(e)
    print(e)
    sys.exit(1)

all_records = []
logger.info("report generation started...")
for record_id in ids_records:
    try:
        record_line = requests.get(conf.item_url.format(record_id)).json()
    except requests.exceptions.RequestException as e:
        logger.error(e)
        print(e)
    if record_line.get("score") >= conf.score:
        date = datetime.date(datetime.fromtimestamp((record_line["time"])))
        if date >= conf.from_date:
            record_line["time"] = datetime.fromtimestamp((record_line["time"])).strftime("%Y-%m-%d-%H:%M:%S")
            all_records.append(record_line)
            logger.info("record {} added to result list".format(record_id))
            pprint(record_line)
print(len(all_records), "records")


def write_dict_to_csv(csv_file, csv_columns, dict_data):
    with open(csv_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        writer.writerows(dict_data)
        logger.info("list of records recorded to file")


logger.info("generation headers list")
rep_columns = set()
for rec in all_records:
    for key in rec.keys():
        rep_columns.add(key)
logger.info(rep_columns)
write_dict_to_csv(conf.results_path + conf.rep_file_name, rep_columns, all_records)
