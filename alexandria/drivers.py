# coding=utf-8

import pprint
import config
import json
import urllib
import requests


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
    def make_request(self, json_data):
        conf = config.alexandria.conf_file
        username = conf.get_driver_parameters("itop", "loginItop")
        password = conf.get_driver_parameters("itop", "passwordItop")
        urlbase = conf.get_driver_parameters("itop", "endpoint")
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

    def get_object(self, ci_type, fields, identifier="name"):
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

        if self.get_object(ci_type, fields, identifier) is not None:
            return self.update_ci(ci_type, fields, identifier)
        else:
            return self.create_ci(ci_type, fields, identifier)

    def set_ci(self, ci):
        org_name = config.alexandria.conf_file.get_driver_parameters(
                "itop", "organization_name")

        brand_id = self.process_ci("Brand", {"name": ci.data.get(
            'Manufacturer', 'Undefined')})

#     "power": serv_data['Oem']['Hp']['PowerAllocationLimit'],

        fields = {"org_id": self.process_ci("Organization",
                                            {"name": org_name}),
                  "name": ci.data.get("Name", "Undefined"),
                  "cpu": ci.data.get('Processors',
                                     {'Count': 'Undefined'})['Count'],
                  "ram": ci.data.get('Memory',
                                     {"TotalSystemMemoryGB": "Undefined"})[
                                         'TotalSystemMemoryGB'],
                  "serialnumber": ci.data.get("SerialNumber", "Undefined"),
                  "brand_id": brand_id,
                  "model_id": self.process_ci("Model", {"name": ci.data.get(
                                                        'Model', "Undefined"),
                                                        "type": "Server",
                                                        "brand_id": brand_id}),
                  }

        server_id = self.process_ci("Server", fields, 'serialnumber')

        [self.process_ci("PhysicalInterface", {"name": i.get('Name',
                                                             'Undefined'),
                                               "macaddress": i.get(
                                               'MACAddress', "Undefined"),
                                               "speed": i.get('SpeedMbps',
                                                              "Undefined"),
                                               "connectableci_id": server_id},
                         'macaddress') for i in ci.interfaces]

        [self.process_ci("FiberChannelInterface", {"name": i.get('name',
                                                                 'Undefined'),
                                                   "wwn": i.get('wwn',
                                                                'Undefined'),
                                                   "speed": i.get('speed',
                                                                  'Undefined'),
                                                   "topology": i.get(
                                                   'topology', 'Undefined'),
                                                   "datacenterdevice_id":
                                                       server_id},
                         'wwn') for i in ci.fc_ports]


class Redfish(Driver):
    def get_ci(self, ci):
        print("Get from redfish")
        import redfish

        print(ci.url_mgmt + " - " + ci.login + " - " + ci.password)

        remote_mgmt = redfish.connect(ci.url_mgmt, ci.login,
                                      ci.password, verify_cert=False,
                                      enforceSSL=False)

#        remote_mgmt = redfish.connect(ci.ip_mgmt, ci.login, ci.password,
#                                      simulator=True, enforceSSL=False)

        system = remote_mgmt.Systems.systems_dict.values()[0]
        ci.ci_type = system.get_parameter("Type")
        ci.data = system.data
        interface_collection = system.ethernet_interfaces_collection
        if interface_collection is not None:
            ci.interfaces = [interface.data for interface in
                             interface_collection.
                             ethernet_interfaces_dict.values()]
        else:
            ci.interfaces = []

        ci.fc_ports = []

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
