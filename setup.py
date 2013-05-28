from setuptools import setup

with open('requirements.txt', 'r') as requirements:
    required_packages = [p.strip() for p in requirements]

setup(
    name='ec2-auto-scaler',
    version='1.0',
    description='An auto-scaling alternative to elastic load balancer in EC2',
    author='Nithin Bose',
    author_email='nithinbose@gmail.com',
    url='https://github.com/nithinbose87/ec2-auto-scaler',
    install_requires=required_packages,
    license='MIT'
)