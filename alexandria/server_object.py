import urllib
import requests
import json
import redfish


def make_request(json_data):
    username = "plop"
    password = "plop"
    urlparams = {'version': '1.0',
                 'auth_user': username,
                 'auth_pwd': password}
    urlbase = "http://16.49.125.115/web/webservices/rest.php"

    urlparams['json_data'] = json.dumps(json_data)
    url = urlbase + '?' + urllib.urlencode(urlparams)
    result = requests.post(url, auth=(username, password))
    if result.status_code != 200:
        raise(requests.HTTPError("Code: {} / Result: {}".format(
            result.status_code, result.text)))
    return result.json().get("objects"), result.text


def get_ci(ci_type, fields, identifier="name"):
    json_data = {"operation": "core/get",
                 "class": ci_type,
                 "output_fields": "*",
                 "key": 'SELECT {} WHERE {} = "{}"'.format(
                     ci_type, identifier, fields[identifier])
                 }
    objects, text = make_request(json_data)
    if objects is not None:
        try:
            return int(objects.values()[0]['key'])
        except:
            raise ValueError("Found an object present but can't find its id")


def create_ci(ci_type, fields, identifier="name"):
    json_data = {"operation": "core/create",
                 "comment": "Synchronization from Alexandria",
                 "class": ci_type,
                 "output_fields": "*",
                 "fields": fields}
    objects, text = make_request(json_data)
    if objects is not None:
        try:
            print("Created CI: {} ({})".format(fields[identifier], ci_type))
            return int(objects.values()[0]['key'])
        except:
            raise ValueError("Created a CI but can't find its id")
    else:
        raise ValueError("Could not create CI: {} ({}) / Error: {}".format(
            fields[identifier], ci_type, text))


def update_ci(ci_type, fields, identifier="name"):
    json_data = {"operation": "core/update",
                 "comment": "Synchronization from Alexandria",
                 "class": ci_type,
                 "output_fields": "*",
                 "key": 'SELECT {} WHERE {} = "{}"'.format(
                     ci_type, identifier, fields[identifier]),
                 "fields": fields
                 }
    objects, text = make_request(json_data)
    if objects is not None:
        try:
            print("Updated CI: {} ({})".format(fields[identifier], ci_type))
            return int(objects.values()[0]['key'])
        except:
            raise ValueError("Updated a CI but can't find its id")
    else:
        raise ValueError("Could not update CI: {} ({}) / Error: {}".format(
            fields[identifier], ci_type, text))


def ci(ci_type, fields, identifier="name"):
    if not isinstance(fields, dict):
        raise TypeError('"fields" should be a dictionary')
    if fields.get(identifier) is None:
        raise TypeError('"fields" should contain'
                        'a "{}" key'.format(identifier))

    if get_ci(ci_type, fields, identifier) is not None:
        return update_ci(ci_type, fields, identifier)
    else:
        return create_ci(ci_type, fields, identifier)


def create_server(o, organization_name="MAAF"):

    brand_id = ci("Brand", {"name": o['brand']})

    fields = {"org_id": ci("Organization", {"name": organization_name}),
              "name": o["name"],
              "cpu": o["cpu"],
              "ram": o["ram"],
              "serialnumber": o["serial"],
              "brand_id": brand_id,
              "model_id": ci("Model", {"name": o['model'], "type": "Server",
                                       "brand_id": brand_id}),
              }

    server_id = ci("Server", fields, 'serialnumber')

    [ci("PhysicalInterface", {"name": i['name'],
                              "macaddress": i['macaddress'],
                              "speed": i['speed'],
                              "connectableci_id": server_id},
     'macaddress') for i in o['interfaces']]

    [ci("FiberChannelInterface", {"name": i['name'],
                                  "wwn": i['wwn'],
                                  "speed": i['speed'],
                                  "topology": i['topology'],
                                  "datacenterdevice_id": server_id},
        'wwn') for i in o['fc_ports']]


remote = redfish.connect('https://172.30.0.87/rest/v1/',
                         'Administrator', 'C8ZXHW3C',
                         verify_cert=False, enforceSSL=False)

serv_data = remote.Systems.systems_dict.values()[0].data


real = {
    "name": serv_data['Name'],
    "cpu": serv_data['Processors']['Count'],
    "ram": serv_data['Memory']['TotalSystemMemoryGB'],
    "brand": serv_data['Manufacturer'],
    "model": serv_data['Model'],
    "serial": serv_data['SerialNumber'],
    "power": serv_data['Oem']['Hp']['PowerAllocationLimit'],
    "interfaces": [],
    "fc_ports": []
}


o = {
    "name": "some_server_42",

    "cpu": "42",
    "ram": "4242",
    "brand": "hoho",
    "model": "DL 42",
    "serial": "plop5plop5plop",
    "interfaces": [{"name": "eth0", "macaddress": "5E:FF:56:A2:AF:42",
                    "speed": 4242},
                   {"name": "eth1", "macaddress": "5E:FF:56:A2:AF:43",
                    "speed": 4242},
                   {"name": "eth1", "macaddress": "5E:FF:56:A2:AF:44",
                    "speed": 42}],
    "fc_ports": [{"name": "plop1", "speed": "42", "topology": "loop",
                  "wwn": "50:00:51:e3:63:a4:49:42"},
                 {"name": "plop2", "speed": "4242", "topology": "fabric",
                  "wwn": "88:00:51:e3:63:a4:49:43"},
                 {"name": "plop2", "speed": "42", "topology": "fabric",
                  "wwn": "88:00:51:e3:63:a4:49:44"}]
}
p = {
    "name": "dsadsadsa",

    "cpu": "54646",
    "ram": "424234",
    "brand": "hoho",
    "model": "DL 59",
    "serial": "pldsadadop5plop5plop",
    "interfaces": [{"name": "eth0", "macaddress": "5E:FF:56:A2:AF:88",
                    "speed": 4242},
                   {"name": "eth1", "macaddress": "5E:FF:56:A2:AF:89",
                    "speed": 42}],
    "fc_ports": [{"name": "plop1", "speed": "42", "topology": "loop",
                  "wwn": "50:00:51:e3:63:a4:49:88"},
                 {"name": "plop2", "speed": "42", "topology": "fabric",
                  "wwn": "88:00:51:e3:63:a4:49:89"}]
}
