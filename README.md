Requirements
---
You need to have HAProxy installed.

* Ubuntu

        $ sudo apt-get install haproxy

Installation
---

    $ git clone git@github.com:nithinbose87/ec2-auto-scaler.git && cd ec2-auto-scaler
    $ python setup.py install
    
Configuration
---

By default ec2-auto-scaler uses the `example/config.ini` file or use `--config` option to specify the config file.

Usage
---

ec2-auto-scaler is designed to run as a daemon from the load balancer itself. 

To start daemon:

    $ python ec2-auto-scaler.py start
    
To stop daemon:

    $ python ec2-auto-scaler.py stop
    
To restart daemon:

    $ python ec2-auto-scaler.py restart

To know the status:

    $ python ec2-auto-scaler.py status


`scaling_interval` in the `main` section of the config file can be used to set the freequency of scaling checks.  

For example, to run every 5 minutes, set `scaling_interval` as follows:

    [main]
    scaling_interval: 300

    
 
