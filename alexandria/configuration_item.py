# coding=utf-8


class ConfigurationItem(object):
    def __init__(self, uuid, url_mgmt, login, password):
        self.uuid = uuid
        self.url_mgmt = url_mgmt
        self.login = login
        self.password = password

        self.ci_parents = []  # List to store parents ci
        self.ci_children = []  # List to store children ci

        # TODO : Maintain a structure to query only the drivers that make
        #        sens for the CI.

    @property
    def ci_type(self):
        return self.__ci_type

    @ci_type.setter
    def ci_type(self, ci_type):
        self.__ci_type = ci_type

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, data):
        self.__data = data
