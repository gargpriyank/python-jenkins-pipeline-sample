#!/usr/bin/python3
#
# rest_data_retrieval_ini_config_update - Python script using REST APIs to retrieve data from REST URL and update it in ini config file.
#
# _author_ = Priyank Garg
#

import argparse
import logging
import requests
import sys
import warnings
import configparser
import math
import socket

warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser(description="Python script using REST APIs to retrieve IP address from REST API and reserve it.")
parser.add_argument('--ini_config_file', help='Pass in the directory path and name of the config yaml file.', dest="ini_config_file", required=True)
parser.add_argument('-url', help='REST API URL', required=True)
parser.add_argument('-user', help='REST API username', required=True)
parser.add_argument('-pwd', help='REST API password', required=True)
args = vars(parser.parse_args())
logging.basicConfig(format='%(message)s', stream=sys.stdout, level=logging.INFO)

def get_set_rest_api_info(ini_config_service="", ip_type=""):
    verify_certificate = False
    server_name = ini_config_service.get("ini_config_service", "server_name")
    if server_name.startswith('"') and server_name.endswith('"'):
        server_name = server_name[1:-1]

    if ip_type == "B":
        server_name = server_name + "b"
    elif ip_type == "I":
        server_name = server_name + "-iDRAC"

    response = requests.get("%s/rest/ip_address_list?WHERE=name='%s'" % (rest_api_url, server_name), verify=verify_certificate, auth=(rest_api_username, rest_api_password))
    if response.status_code != 200:
        logging.error("No data found in REST API for the server: %s", server_name)
        sys.exit()
    else:
        rest_api_data = response.json()
        if len(rest_api_data) == 0:
            logging.error("No data found in REST API for the server: %s", server_name)
            sys.exit()
        elif len(rest_api_data) > 1:
            logging.error("There are multiple records in REST API for the server: %s", server_name)
            sys.exit()
        else:
            resloved_ip_list = []
            try:
                resolved_ip_response = socket.getaddrinfo(server_name, 0)
                for resolved_ip in resolved_ip_response:
                    resloved_ip_list.append(resolved_ip[-1][0])
            except Exception:
                raise Exception("Host: " + server_name + " is not resolvable") from None
                
            for rest_api_items in rest_api_data:
                gateway = ''
                logging.info("Retrieved IP address: %s", rest_api_items['ip'])
                for ip_class_parameters_items in rest_api_items['ip_class_parameters'].split('&'):
                    if 'ea_gateway' in ip_class_parameters_items:
                        gateway = ip_class_parameters_items.split('=')[1]
                        logging.info("Retrieved Gateway: %s", gateway)
                        break
                if ip_type == "B":
                    subnet_size = rest_api_items['subnet_size']
                    ini_config_service.set("ini_config_service", "back_ip", '"' + rest_api_items['back_ip'] + '"')
                    ini_config_service.set("ini_config_service", "back_gateway", '"' + gateway + '"')
                    ini_config_service.set("ini_config_service", "back_mask", '"' + get_network_mask(subnet_size) + '"')
                elif ip_type == "I":
                    ini_config_service.set("ini_config_service", "idrac_ip", '"' + rest_api_items['idrac_ip'] + '"')
                else:
                    subnet_size = rest_api_items['subnet_size']
                    ini_config_service.set("ini_config_service", "primary_ip", '"' + rest_api_items['primary_ip'] + '"')
                    ini_config_service.set("ini_config_service", "primary_gateway", '"' + gateway + '"')
                    ini_config_service.set("ini_config_service", "primary_mask", '"' + get_network_mask(subnet_size) + '"')

def write_to_ini_config(ini_config_service=""):
    with open(args["ini_config_file"], "w") as file:
        ini_config_service.write(file, space_around_delimiters=False)
    with open(args["ini_config_file"], "r") as file:
        file_data = file.read().splitlines(True)
    with open(args["ini_config_file"], "w") as file:
        file.writelines(file_data[1:])

def use_ini_config_file():
    global rest_api_url
    global rest_api_username
    global rest_api_password

    ini_config_service = configparser.RawConfigParser()
    ini_config_service.optionxform = str
    with open(args["ini_config_file"]) as stream:
        ini_config_service.read_string("[ini_config_service]\n" + stream.read())
        get_set_rest_api_info(ini_config_service, "R")
        get_set_rest_api_info(ini_config_service, "B")
        get_set_rest_api_info(ini_config_service, "I")
        write_to_ini_config(ini_config_service)

def get_network_mask(subnet_size):
    cidr = 32 - math.ceil(math.log(int(subnet_size)) / math.log(2))
    network_mask = (0xffffffff >> (32-cidr)) << (32-cidr)
    return (str((0xff000000 & network_mask) >> 24) + '.' +
            str((0x00ff0000 & network_mask) >> 16) + '.' +
            str((0x0000ff00 & network_mask) >> 8) + '.' +
            str((0x000000ff & network_mask)))

if __name__ == "__main__":
    if args["ini_config_file"]:
        if args["url"]:
            rest_api_url = args["url"]
        if args["user"]:
            rest_api_username = args["user"]
        if args["pwd"]:
            rest_api_password = args["pwd"]

        use_ini_config_file()
        sys.exit(0)
    else:
        logging.error("\n- FAIL, invalid argument values or not all required parameters passed in.")
