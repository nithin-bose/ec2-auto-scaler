class ConfigFileError(Exception):
    def __init__(self):
        self.message = 'Error in config file'

    def __str__(self):
        return self.message


class ScaleError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class InvalidPricingOption(Exception):
    def __init__(self, node_option):
        self.message = 'Option %s does not exist' % node_option

    def __str__(self):
        return self.message


class InstanceTerminationFailed(Exception):
    def __init__(self):
        self.message = 'Instance termination failed. Cannot scale-down.'

    def __str__(self):
        return self.message


class InvalidStateError(Exception):
    def __init__(self, state):
        self.message = 'State %s does not exist' % state

    def __str__(self):
        return self.message


class InstancesNotSetError(Exception):
    def __init__(self):
        self.message = 'Instances should be set before LB can be reconfigured.'

    def __str__(self):
        return self.message
