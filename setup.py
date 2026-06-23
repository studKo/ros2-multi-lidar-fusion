from setuptools import setup


package_name = 'lidar_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', [
            'launch/lidars_launch.py',
            'launch/foxglove_launch.py'
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='studKo',
    maintainer_email='studKo@users.noreply.github.com',
    description='Integrated control for TG30 and GS2 LiDARs',
    license='MIT',
    entry_points={
        'console_scripts': [
            'controller = lidar_control.controller:main',
            'gs2_bypasser = lidar_control.gs2_bypasser:main',
            'tg30_bypasser = lidar_control.tg30_bypasser:main',
        ],
    },
)