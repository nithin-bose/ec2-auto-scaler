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


class InstanceLaunchTimeOut(Exception):
    def __init__(self):
        self.message = 'Timed out. Cannot launch instance.'

    def __str__(self):
        return self.message


class SpotRequestTimeOut(Exception):
    def __init__(self):
        self.message = 'Timed out. Cannot complete spot request.'

    def __str__(self):
        return self.message


class UnknownProviderError(Exception):
    def __init__(self):
        self.message = 'Unknown provider specified in config file.'

    def __str__(self):
        return self.message


class UnknownLoadBalancerError(Exception):
    def __init__(self):
        self.message = 'Unknown load balancer specified in config file.'

    def __str__(self):
        return self.message