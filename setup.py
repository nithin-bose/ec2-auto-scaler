from setuptools import setup

setup(name='ec2-auto-scaler',
      version='1.0',
      description='An auto-scaling alternative to elastic load balancer in EC2',
      author='Nithin Bose',
      author_email='nithinbose@gmail.com',
      url='https://github.com/nithinbose87/ec2-auto-scaler',
      install_requires=['boto>=2.9.3', 'mako>=0.8.0', 'argparse>=1.2.1'],
      license='MIT')