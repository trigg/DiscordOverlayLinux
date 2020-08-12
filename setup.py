from setuptools import setup, find_packages

def readme():
    return open('README.md', 'r').read()

setup(
    name = 'discordoverlaylinux',
    author = 'trigg',
    author_email = 'triggerhapp@gmail.com',
    version = '0.0.2',
    description = 'Unofficial Discord Overlay for Linux',
    long_description = readme(),
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/trigg/DiscordOverlayLinux',
    packages = find_packages(),
    include_package_data = True,
    data_files = [
        ('share/applications', ['discord-overlay.desktop']),
        ('share/icons', ['discord-overlay.png']),
    ],
    install_requires = [
        'PyQt5',
        'PyQt5-sip',
        'PyQtWebEngine',
        'pyxdg',
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
