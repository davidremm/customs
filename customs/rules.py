# -*- coding: utf-8; -*-
import os
import tempfile
from hashlib import md5

import yaml
from yaml import SafeLoader, YAMLError

from customs.utils import normalize_keys

class Rules(object):

    def __init__(self, name:str, rules_data:str=None):
        """
        :return:
        """
        self._checks        = {}
        self._metadata      = {}
        self._name          = name
        self._service_regex = None
        self._tags          = []
        self.__load(rules_data)

        if 'id' not in self._metadata:
            self._metadata['id'] = True
    ##
    # class methods
    ##
    @classmethod
    def create(cls, service:str='default'):
        with tempfile.NamedTemporaryFile() as tmp:
            # write message to the user explaining whats going on.
            tmp.write(
                "##\n"
                "# This file was generated by customs.\n"
                "# The file must valid yaml and is required to use the customs agent.\n"
                "# Please fill out the following values with their respective data types.\n"
                "##\n".encode('utf-8')
            )

            # write configuration template to tmp file for user.
            tmp.write(
                yaml.safe_dump(cls.default_template(), default_flow_style=False).encode('utf-8')
            )

            tmp.flush()
            os.system('{0} {1}'.format(os.getenv('EDITOR'), tmp.name))
            tmp.seek(0)

            return Rules(service, tmp.read().decode('utf-8'))

    @classmethod
    def default_template(cls) -> dict:
        return {
            'checks': {
                'check': '(str) – The path to the check script to run',
                'interval': '(str) – The check execution interval',
                'ttl': '(str) – The TTL for external script check pings',
                'httpcheck': '(str) – An URL to check every interval'
            },
            'metadata': {
                "id": True,
                "created": True,
                "driver": True,
                "exec_driver": True,
                "host_config": {
                    "binds": True,
                    "memory": True,
                    "memory_swap": True,
                    "cpu_shares": True,
                    "cpu_period": True,
                    "cpuset_cpus": True,
                    "cpuset_mems": True,
                    "cpu_quota": True,
                    "blkio_weight": True,
                    "memory_swappiness": True,
                    "privileged": True,
                    "port_bindings": True,
                    "links": True,
                    "publish_all_ports": True,
                    "dns": True,
                    "dns_search": True,
                    "extra_hosts": True,
                    "volumes_from": True,
                    "devices": True,
                    "network_mode": True,
                    "cap_add": True,
                    "cap_drop": True,
                    "group_add": True,
                    "restart_policy": True,
                    "readonly_rootfs": True,
                    "ulimits": True,
                    "log_config": True,
                },
                "mounts": True,
                "config": {
                    "hostname": True,
                    "domainname": True,
                    "user": True,
                    "exposed_ports": True,
                    "image": True,
                    "volumes": True
                },
                "network_settings": True
            },
            'service_regex': '.*',
            'tags': [
                'docker',
                'inspect.config.labels=com.freight-forwarder.project',
                'inspect.config.labels=com.freight-forwarder.team',
                'inspect.config.labels=com.freight-forwarder.type'
            ]
        }

    ##
    # properties
    ##
    @property
    def checks(self) -> dict:
        return self._checks

    @property
    def metadata(self) -> dict:
        return self._metadata

    @property
    def tags(self) -> list:
        return self._tags

    @property
    def name(self) -> str:
        return self._name

    @property
    def service_regex(self) -> str:
        return self._service_regex

    ##
    # public methods
    ##
    def edit(self):
        with tempfile.NamedTemporaryFile() as tmp:
            # write configuration template to tmp file for user.
            tmp.write(
               self.to_yaml().encode('utf-8')
            )

            tmp.flush()
            editor = os.getenv('EDITOR')
            if not editor:
                raise OSError('Please add "export EDITOR=subl -w" to your profile or something equivalent.')

            os.system('{0} {1}'.format(editor, tmp.name))
            tmp.seek(0)

            self.__load(tmp.read().decode('utf-8'))

    def to_dict(self) -> dict:
        return {name: getattr(self, name) for name in dir(self) if not name.startswith('_') and not callable(getattr(self, name))}

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.to_dict(), default_flow_style=False, allow_unicode=True)

    def md5sum(self):
        return md5(self.to_yaml().encode()).hexdigest()

    ##
    # private methods
    ##
    def __load(self, rules_data:str) -> None:
        """
        loads a yaml str, serializes and normalized the rule data. Then assigns the rule data to properties.
        :param config_file: A :string: loaded from a yaml file.
        """
        if not isinstance(rules_data, str):
            raise TypeError('rules_data must be a str.')

        try:
            data = SafeLoader(rules_data).get_data()

            if data is None:
                raise AttributeError('The rules must have data in it.')

            data = normalize_keys(data, snake_case=False)
            for key, value in data.items():
                variable_name = '_{0}'.format(key)
                if hasattr(self, variable_name):
                    setattr(self, variable_name, value)
                else:
                    raise AttributeError('{0} isn\'t a valid rule attribute.'.format(key))

        except YAMLError as e:
            if hasattr(e, 'problem_mark'):
                raise SyntaxError(
                    "There is a syntax error in the rules line: {0} column: {1}".format(
                        e.problem_mark.line,
                        e.problem_mark.column
                    )
                )
            else:
                raise SyntaxError("There is a syntax error in the rules.")