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

By default ec2-auto-scaler uses the example/config.ini file or use `--config` option to specify the config file.

Usage
---

ec2-auto-scaler was designed to be run from the load balancer itself as a cron job. 
Ideally it would be run every minute.

    $ python ec2-auto-scaler.py
