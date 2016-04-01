"""
Name: VM manager

Date Created: January 25, 2016

Created By:
    Shubam Mehta

Purpose: Create, start, terminate and delete google cloud virtual machines via this script

"""

# Installing python on vm:
# mkdir test
# cd test/
# wget https://www.python.org/ftp/python/3.5.1/Python-3.5.1.tgz
# tar -xvf Python-3.5.1.tgz
# cd Python-3.5.1/
# apt-get install build-essential
# ./configure
# make install


import json
import time
import os

from config import logger, PROJECT_NAME, NETWORK_NAME, get_compute_engine_credentials
from apiclient import discovery

DEFAULT_VM_ZONE = "us-central1-f"


def list_vm_instances(project=PROJECT_NAME, zone=DEFAULT_VM_ZONE):
    try:
        compute = discovery.build('compute', 'v1', credentials=get_compute_engine_credentials())
        req = compute.instances().list(project=project, zone=zone)
        response = req.execute()
        print(json.dumps(response['items'], indent='\n'))
        return response

    except Exception as e:
        logger.debug("Unable to list instances: %s" % e)


def create_disk_for_vm(name, source_image, disk_size, zone=DEFAULT_VM_ZONE, project=PROJECT_NAME):
    """
    Creates disk on Google Cloud compute engine to be used alongside a vm. Disk is generated from
    an image that is also stored on Google Cloud compute engine

    :param name: Name of disk (Usually same name as VM_name)
    :param source_image: Image for disk to replicate (stored on google cloud compute engine/ images)
    :param disk_size: Size of disk
    :param zone: The zone the disk should be created in (same as VM zone)
    :param project: Name of project
    :return: Link of disk if successful, False if unsuccessful
    """
    try:
        compute = discovery.build('compute', 'v1', credentials=get_compute_engine_credentials())

        config = {
            'name': name,
            'description': '',
            'sizeGb': disk_size,
            'sourceImage': source_image,
        }

        req = compute.disks().insert(project=project, zone=zone, body=config)
        resp = req.execute()

        completed = wait_for_operation(project, zone, resp['name'])

        if completed == 'DONE':
            link = resp['targetLink'].split('/v1/')[1]
            return link

    except Exception as e:
        logger.debug("Creation of disk failed: %s" % e)
        print(e)
        return False


def get_instance(name, zone=DEFAULT_VM_ZONE, project=PROJECT_NAME):
    """
    Gets the information of the instance

    :param name: Name of instance as specified on google cloud
    :param zone: Zone the VM exists in
    :param project: Name of Project
    :return: Json object containing information on instance specified
    """

    try:
        logger.info("Getting information for VM %s." % name)

        compute = discovery.build('compute', 'v1', credentials=get_compute_engine_credentials())
        req = compute.instances().get(project=project, zone=zone, instance=name)
        response = req.execute()

        return response

    except Exception as e:
        logger.debug("Failed: %s" % e)


def get_ip_address_of_vm(name, zone=DEFAULT_VM_ZONE, project=PROJECT_NAME):
    """
    Gets the IP address of the instance

    :param name: Name of instance as specified on google cloud
    :param zone: Zone the VM exists in
    :param project: Name of Project
    :return: IP address of VM specified
    """
    try:
        logger.info("Getting IP address of VM %s." % name)

        compute = discovery.build('compute', 'v1', credentials=get_compute_engine_credentials())
        req = compute.instances().get(project=project, zone=zone, instance=name)
        response = req.execute()

        logger.info("Completed")

        return response['networkInterfaces'][0]['accessConfigs'][0]['natIP']

    except Exception as e:
        logger.debug("Failed: %s" % e)


def create_instance(name, disk_size, source_image=None, num_cores=2, zone=DEFAULT_VM_ZONE, project=PROJECT_NAME,
                    network=NETWORK_NAME):
    """
    Creates vm_instances with disks that hold ftp distributor and retriever code.

    :param name: Name of VM instance
    :param disk_size: Size of disk
    :param num_cores: Number of cores you want the VM to have.
                      Options: Micro, small, 1, 2, 4, 8, 16, 32
    :param zone: The zone you want instantiate the VM in
    :param project: The project the VM is created under
    :param network: The network the VM is created under
    :return: True or False
    """

    try:
        logger.info("Creating VM named %s" % name)

        startup_script = open(
            os.path.join(os.path.dirname(__file__), 'startup-script.sh'), 'r'
        ).read()

        machine = {
            'micro': 'f1-micro',
            'small': 'g1-small',
                '1': 'n1-standard-1',
                '2': 'n1-standard-2',
                '4': 'n1-standard-4',
                '8': 'n1-standard-8',
               '16': 'n1-standard-16',
               '32': 'n1-standard-32'
        }[str(num_cores)]
        machine_type = 'projects/%s/zones/%s/machineTypes/%s' % (project, zone, machine)

        disk_image = create_disk_for_vm(name, "global/images/remotex-image-testing", disk_size)

        # Use this if you want to create vm directly from VM
        # disk_image = 'projects/skywatch-app/global/images/remotex-image'
        # disk_type = 'projects/%s/zones/%s/diskTypes/pd-standard' % (project, zone)

        if disk_image is False:
            return False

        network = "projects/%s/global/networks/%s" % (project, network)

        # Config that specifies specifications of vm
        config = {
            'name': name,                          # Name of instance
            # 'zone': zone,                          # Zone chosen for instance (There are zone quotas)
            'machineType': machine_type,           # Machine Type for vm (dependent on zone)
            'description': '',                     # Description for vm instance (Optional)
            'canIpForward': False,                 # Needed only if we plan to forward routes from instance
            'networkInterfaces': [                  # Specifies how this interface interacts with internet
                {
                    'network': network,                       # Default Network access
                    'accessConfigs': [                        # Array of configurations for the interface
                        {'type': 'ONE_TO_ONE_NAT',            # Only option available
                         'name': 'External NAT'}              # Name can be anything
                                                              # Can also specify natIP or left blank
                    ],
                }
            ],
            'metadata': {
                "items": [
                    {
                        'key': 'startup-script',
                        'value': startup_script
                    },
                    {
                        'key': 'vm_name',
                        'value': name
                    },
                    # {
                    #     'key': 'vm_start_time',              #Can be used to figure out cost of running vm
                    #     'value': START
                    # },
                    {
                        'key': 'vm_disk_size',
                        'value': disk_size
                    },
                    {
                        'key': 'vm_machine_type',
                        'value': machine_type
                    }
                ]
            },
            'tags': {
                "items": [
                    "http-server",
                    "https-server"
                ]
            },
            'disks': [                              # Lists an array of disks associated with this instance
                {
                    "index": 0,                     # Index of disk attached with vm (can be more than one)
                    "type": 'PERSISTENT',           # Can be SCRATCH or PERSISTENT (default = PERSISTENT)
                    "mode": 'READ_WRITE',           # Can be READ_WRITE (default) or READ_ONLY
                    "source": disk_image,             # Specifies a valid partial or full URL to an existing
                                                    #    Persistent Disk resource. This field is only
                                                    #    applicable for persistent disks when creating from existing
                    "deviceName": name,
                    "boot": True,                   # Indicates that this is boot disk
                    # "initializeParams": {           # Parameters for this disk
                    #    "sourceImage": disk_image,  # Disk image you want to use (can be custom image)
                    #    "diskSizeGb": 10,    # Size of disk
                    #    "diskType": disk_type       # Disk type to use to create instance
                    # },                              #   can be pd-standard, pd-ssd, local-ssd
                    "autoDelete": True,
                }
            ],
            'serviceAccounts': [
                {
                    'email': 'default',
                    'scopes':
                    [
                        'https://www.googleapis.com/auth/devstorage.read_write',
                        'https://www.googleapis.com/auth/logging.write'
                    ]
                }
            ],
        }

        compute = discovery.build('compute', 'v1', credentials=get_compute_engine_credentials())
        req = compute.instances().insert(project=project, zone=zone, body=config)
        resp = req.execute()

        wait_for_operation(project, zone, resp['name'])

        logger.debug("Completed creating VM named %s." % name)

        return True

    except Exception as e:
        logger.debug("Unable to create instance: %s" % e)
        print(("Unable to create instance: %s" % e))
        return False


def delete_instance(name, zone=DEFAULT_VM_ZONE):
    """
    Deletes VM instance on Google Cloud compute Engine

    :param name: Name of VM instance you want to delete
    :param zone: Zone of VM instance you want to delete
    :return: True or False
    """
    try:
        logger.info("Deleting VM named %s." % name)

        compute = discovery.build('compute', 'v1', credentials=get_compute_engine_credentials())
        req = compute.instances().delete(project=PROJECT_NAME, zone=zone, instance=name)
        response = req.execute()

        wait_for_operation(PROJECT_NAME, zone, response['name'])

        logger.info('Deletion successful!')

        return True

    except Exception as e:
        logger.debug("Deletion of VM %s failed: %s" % e)
        return False


def wait_for_operation(project, zone, operation):
    """
    Checks if operation demanded (create/start/stop/delete) is completed

    :param project: Project name on google cloud
    :param zone: zone the vm_instance resides in
    :param operation: which operation is being run
    :return: True when completed
    """
    logger.debug('Waiting for operation to finish...')

    while True:
        try:
            compute = discovery.build('compute', 'v1', credentials=get_compute_engine_credentials())
            req = compute.zoneOperations().get(
                project=project,
                zone=zone,
                operation=operation
            )
            result = req.execute()

            if result['status'] == 'DONE':
                return result['status']

            time.sleep(1)
        except Exception as e:
            logger.debug('Checking if operation is completed failed: %s' % e)
