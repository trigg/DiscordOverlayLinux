from setuptools import setup, find_packages

def readme():
    return open('README.md', 'r').read()

setup(
    name = 'discordoverlaylinux',
    author = 'trigg',
    author_email = 'triggerhapp@gmail.com',
    version = '0.0.1',
    description = 'Unofficial Discord Overlay for Linux',
    long_description = readme(),
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/trigg/DiscordOverlayLinux',
    packages = find_packages(),
    include_package_data = True,
    install_requires = [
        'PyQt5 == 5.14.2',
        'PyQt5-sip == 12.7.2',
        'PyQtWebEngine == 5.14.0',
        'pyxdg == 0.26',
    ],
    entry_points = {
        'console_scripts': [
            'discord-overlay = discord_overlay.discord_overlay:entrypoint',
        ]
    },
    classifiers = {
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Communications :: Chat',
        'Topic :: Communications :: Conferencing',
    },
    keywords = 'discord overlay linux',
    license = 'GPLv3+',
)
