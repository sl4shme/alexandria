# coding=utf-8

import pprint
import config
import json
import urllib
import requests

# remote = redfish.connect('https://172.30.0.87/rest/v1/',
#                          'Administrator', 'C8ZXHW3C',
#                          verify_cert=False, enforceSSL=False)
#
# serv_data = remote.Systems.systems_dict.values()[0].data
#
#
# real = {
#     "name": serv_data['Name'],
#     "cpu": serv_data['Processors']['Count'],
#     "ram": serv_data['Memory']['TotalSystemMemoryGB'],
#     "brand": serv_data['Manufacturer'],
#     "model": serv_data['Model'],
#     "serial": serv_data['SerialNumber'],
#     "power": serv_data['Oem']['Hp']['PowerAllocationLimit'],
#     "interfaces": [],
#     "fc_ports": []
# }
#
#
# o = {
#     "name": "some_server_42",
#
#     "cpu": "42",
#     "ram": "4242",
#     "brand": "hoho",
#     "model": "DL 42",
#     "serial": "plop5plop5plop",
#     "interfaces": [{"name": "eth0", "macaddress": "5E:FF:56:A2:AF:42",
#                     "speed": 4242},
#                    {"name": "eth1", "macaddress": "5E:FF:56:A2:AF:43",
#                     "speed": 4242},
#                    {"name": "eth1", "macaddress": "5E:FF:56:A2:AF:44",
#                     "speed": 42}],
#     "fc_ports": [{"name": "plop1", "speed": "42", "topology": "loop",
#                   "wwn": "50:00:51:e3:63:a4:49:42"},
#                  {"name": "plop2", "speed": "4242", "topology": "fabric",
#                   "wwn": "88:00:51:e3:63:a4:49:43"},
#                  {"name": "plop2", "speed": "42", "topology": "fabric",
#                   "wwn": "88:00:51:e3:63:a4:49:44"}]
# }
# p = {
#     "name": "dsadsadsa",
#
#     "cpu": "54646",
#     "ram": "424234",
#     "brand": "hoho",
#     "model": "DL 59",
#     "serial": "pldsadadop5plop5plop",
#     "interfaces": [{"name": "eth0", "macaddress": "5E:FF:56:A2:AF:88",
#                     "speed": 4242},
#                    {"name": "eth1", "macaddress": "5E:FF:56:A2:AF:89",
#                     "speed": 42}],
#     "fc_ports": [{"name": "plop1", "speed": "42", "topology": "loop",
#                   "wwn": "50:00:51:e3:63:a4:49:88"},
#                  {"name": "plop2", "speed": "42", "topology": "fabric",
#                   "wwn": "88:00:51:e3:63:a4:49:89"}]
# }


class Driver(object):
    def __init__(self):
        self.driver_type = self.__class__.__name__
        # Get credentials from conf files for CMDB
        pass

    def get_driver_type(self):
            return self.driver_type

    def get_ci(self, ci):
        pass

    def set_ci(self, ci):
        pass


class Itop(Driver):
    def __init__(self):
        super(Itop, self).__init__()
        self.conf = config.alexandria.conf_file

    def make_request(self, json_data):
        username = self.conf.get_driver_parameters("itop", "loginItop")
        password = self.conf.get_driver_parameters("itop", "passwordItop")
        urlbase = self.conf.get_driver_parameters("itop", "endpoint")
        urlparams = {'version': '1.0',
                     'auth_user': username,
                     'auth_pwd': password}

        urlparams['json_data'] = json.dumps(json_data)
        url = urlbase + '?' + urllib.urlencode(urlparams)
        result = requests.post(url, auth=(username, password))
        if result.status_code != 200:
            raise(requests.HTTPError("Code: {} / Result: {}".format(
                result.status_code, result.text)))
        return result.json().get("objects"), result.text

    def get_ci(self, ci_type, fields, identifier="name"):
        json_data = {"operation": "core/get",
                     "class": ci_type,
                     "output_fields": "*",
                     "key": 'SELECT {} WHERE {} = "{}"'.format(
                         ci_type, identifier, fields[identifier])
                     }
        objects, text = self.make_request(json_data)
        if objects is not None:
            try:
                return int(objects.values()[0]['key'])
            except:
                raise ValueError("Found an object present "
                                 "but can't find its id")

    def create_ci(self, ci_type, fields, identifier="name"):
        json_data = {"operation": "core/create",
                     "comment": "Synchronization from Alexandria",
                     "class": ci_type,
                     "output_fields": "*",
                     "fields": fields}
        objects, text = self.make_request(json_data)
        if objects is not None:
            try:
                print("Created CI: {} ({})".format(fields[identifier],
                                                   ci_type))
                return int(objects.values()[0]['key'])
            except:
                raise ValueError("Created a CI but can't find its id")
        else:
            raise ValueError("Could not create CI: {} ({}) / Error: {}".format(
                fields[identifier], ci_type, text))

    def update_ci(self, ci_type, fields, identifier="name"):
        json_data = {"operation": "core/update",
                     "comment": "Synchronization from Alexandria",
                     "class": ci_type,
                     "output_fields": "*",
                     "key": 'SELECT {} WHERE {} = "{}"'.format(
                         ci_type, identifier, fields[identifier]),
                     "fields": fields
                     }
        objects, text = self.make_request(json_data)
        if objects is not None:
            try:
                print("Updated CI: {} ({})".format(fields[identifier],
                                                   ci_type))
                return int(objects.values()[0]['key'])
            except:
                raise ValueError("Updated a CI but can't find its id")
        else:
            raise ValueError("Could not update CI: {} ({}) / Error: {}".format(
                fields[identifier], ci_type, text))

    def process_ci(self, ci_type, fields, identifier="name"):
        if not isinstance(fields, dict):
            raise TypeError('"fields" should be a dictionary')
        if fields.get(identifier) is None:
            raise TypeError('"fields" should contain'
                            'a "{}" key'.format(identifier))

        if self.get_ci(ci_type, fields, identifier) is not None:
            return self.update_ci(ci_type, fields, identifier)
        else:
            return self.create_ci(ci_type, fields, identifier)

    def create_server(self, o, org_name=None):
        if org_name is None:
            org_name = self.conf.get_driver_parameters("itop",
                                                       "organization_name")

        brand_id = self.process_ci("Brand", {"name": o['brand']})

        fields = {"org_id": self.process_ci("Organization",
                                            {"name": org_name}),
                  "name": o["name"],
                  "cpu": o["cpu"],
                  "ram": o["ram"],
                  "serialnumber": o["serial"],
                  "brand_id": brand_id,
                  "model_id": self.process_ci("Model", {"name": o['model'],
                                                        "type": "Server",
                                                        "brand_id": brand_id}),
                  }

        server_id = self.process_ci("Server", fields, 'serialnumber')

        [self.process_ci("PhysicalInterface", {"name": i['name'],
                                               "macaddress": i['macaddress'],
                                               "speed": i['speed'],
                                               "connectableci_id": server_id},
                         'macaddress') for i in o['interfaces']]

        [self.process_ci("FiberChannelInterface", {"name": i['name'],
                                                   "wwn": i['wwn'],
                                                   "speed": i['speed'],
                                                   "topology": i['topology'],
                                                   "datacenterdevice_id":
                                                       server_id},
                         'wwn') for i in o['fc_ports']]

    def set_ci(self, ci):
        username = self.conf.get_driver_parameters("itop", "loginItop")
        password = self.conf.get_driver_parameters("itop", "passwordItop")
        config.logger.debug("login : {}, password : {}".format(
                                                               username,
                                                               password
                                                               )
                            )
        # Craft request body and header
        urlbase = self.conf.get_driver_parameters("itop", "endpoint")

        request = '{"operation":"core/create","comment":"Synchronization'\
                  + ' from Alexandria","class":"Server","output_fields":'\
                  + '"id,name,ram", "fields":{"org_id": "3","name":"'\
                  + ci.data["Name"] + '","ram":"'\
                  + format((ci.data["MemorySummary"])["TotalSystemMemoryGiB"])\
                  + '","serialnumber":"' + ci.data["SerialNumber"] + '"}}'

        urlparam = {'version': '1.0',
                    'auth_user': username,
                    'auth_pwd': password,
                    'json_data': request
                    }

        # header = {'Content-type': 'application/json'}

        url = urlbase + '?' + urllib.urlencode(urlparam)

        config.logger.debug(url)

        # =======================================================================
        # answer = requests.post(url,
        #                      headers=header,
        #                      verify="False"
        #                     )
        # =======================================================================
        answer = requests.post(url, auth=(username, password))

        config.logger.debug(answer.status_code)
        config.logger.debug(answer.text)


class Redfish(Driver):
    def get_ci(self, ci):
        print("Get from redfish")
        import redfish

        print(ci.ip_mgmt + " - " + ci.login + " - " + ci.password)

        # remote_mgmt = redfish.connect(ci.ip_mgmt, ci.login,
        #                               ci.password, verify_cert=False)
        remote_mgmt = redfish.connect(ci.ip_mgmt, ci.login, ci.password,
                                      simulator=True, enforceSSL=False)

        ci.ci_type = remote_mgmt.Systems.systems_list[0].get_parameter(
                "@odata.type")
        ci.data = remote_mgmt.Systems.systems_list[0].get_parameters()

        # print("Redfish API version"
        #       " : {} \n".format(remote_mgmt.get_api_version()))
        return True

    def set_ci(self, ci):
        print("Push to Redfish")
        return True


class Ironic(Driver):
    pass


class Mondorescue(Driver):
    pass


class Fakecmdb(Driver):
    def set_ci(self, ci):
        # Determine ci type so we can do the proper action.
        pp = pprint.PrettyPrinter(indent=4)
        if ci.ci_type == "Manager":
            print("We are in Fakecmdb driver !")
            pp.pprint(ci.data)
            # Simply write a json file with ci.data content.
            with open("Fakecmdb.json", "w") as jsonfile:
                json.dump(ci.data, jsonfile, indent=4)
            jsonfile.close()

        #
        # ====================================================================


class Fakeprovider(Driver):
    def get_ci(self, ci):
        # Simulate a driver that will provide Manager data.

        # TODO a connect method must be implemented

        # Assuming the connection is ok.

        # Now create a copy of manager model from reference model.
        # ci.ci_type = "Manager"
        # ci.data = config.alexandria.model.get_model("Manager")

        #  Update the structure with data
        #  TODO : think to encapsulate to not edit ci.data directly.
        #         This could be also a way to check source of truth.
        #         If data provided by our driver is not the source of truth
        #         then discard it.

        # ci.data["ManagerType"] = "BMC"
        # ci.data["Model"] = "Néné Manager"
        # ci.data["FirmwareVersion"] = "1.00"

        # if ci.data is config.alexandria.model.Manager:
        #    print "identical"

        pp = pprint.PrettyPrinter(indent=4)

        pp.pprint(ci.ci_type)


class DriverCollection(list):
    pass
