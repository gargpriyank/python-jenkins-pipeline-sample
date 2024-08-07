#!/usr/bin/python3
#
# git_service - Python script calling GIT APIs for data retrieval.
#
# _author_ = Priyank Garg
#

import argparse
import logging
import requests
import sys
import warnings
import json

warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser(description="Python script calling git APIs for data retrieval.")
parser.add_argument('-url', help='git Default Reviewer URL', required=True)
parser.add_argument('-user', help='REST API username', required=True)
parser.add_argument('-pwd', help='REST API password', required=True)
parser.add_argument('-project', help='GIT project', required=True)
parser.add_argument('-repo', help='GIT repo', required=True)
args = vars(parser.parse_args())
logging.basicConfig(format='%(message)s', stream=sys.stdout, level=logging.INFO)

def getDefaultReviewers():
    global git_url
    global git_username
    global git_password
    global git_project
    global git_repo
    json_reviewers = []

    verify_certificate = False

    response = requests.get("%s/projects/%s/repos/%s/conditions" % (git_url, git_project, git_repo), verify=verify_certificate, auth=(git_username, git_password))
    if response.status_code != 200 and response.status_code != 201:
        logging.error("Error getting default reviewers. Status code: %s", response.status_code)
    else:
        git_data = response.json()
        for git_items in git_data:
            for reviewer_items in git_items['reviewers']:
                reviewer = {"user": {"name": None}}
                reviewer['user']['name'] = reviewer_items['name']
                json_reviewers.append(reviewer)
    return json.dumps(json_reviewers)

if __name__ == "__main__":
    if args["url"]:
        git_url = args["url"]
    if args["user"]:
        git_username = args["user"]
    if args["pwd"]:
        git_password = args["pwd"]
    if args["project"]:
        git_project = args["project"]
    if args["repo"]:
        git_repo = args["repo"]

    reviewers = getDefaultReviewers()
    logging.info(reviewers)
    sys.exit(0)