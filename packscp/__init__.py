# -*- coding: utf-8 -*-


import datetime
import hashlib
import logging
import pathlib
import subprocess


table_file_name = 'hash_table.txt'


def pack(target_file_list, logger=None):
    # logger
    if logger is None:
        logger = logging.getLogger(__name__)
    logger.info('pack: {0}'.format(', '.join(map(str, target_file_list))))
    # create temp directory
    temp_directory = pathlib.Path(
            datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    logger.info('mkdir {0}'.format(temp_directory))
    temp_directory.mkdir()
    # create table
    hashed_name_list = []
    table_file = temp_directory.joinpath(table_file_name)
    with table_file.open(mode='w') as table:
        for target_file in target_file_list:
            # hash
            hashed_name = hashlib.sha256(target_file.name.encode())
            logger.info('{0}: "{1}" -> {2}'.format(
                    hashed_name.name,
                    target_file.name,
                    hashed_name.hexdigest()))
            # duplication check
            if hashed_name.hexdigest() in hashed_name_list:
                logger.error('dupicated: "{0}" -> "{1}"'.format(
                        target_file.name,
                        hashed_name.hexdigest()))
                continue
            hashed_name_list.append(hashed_name.hexdigest())
            # create symbolic link
            temp_directory.joinpath(hashed_name.hexdigest()) \
                          .symlink_to(target_file.resolve())
            # write table
            table.write('{0}\t{1}\n'.format(
                    hashed_name.hexdigest(),
                    target_file.name))
    return temp_directory


def scp(source, destination, logger=None):
    # logger
    if logger is None:
        logger = logging.getLogger(__name__)
    logger.info('scp: {0} -> {1}'.format(source, destination))
    # scp
    subprocess.run(
            args=['scp', '-r', source, destination],
            check=True)


def unpack(target_directory, logger=None):
    # logger
    if logger is None:
        logger = logging.getLogger(__name__)
    logger.info('unpack: {0}'.format(target_directory))
    # open table
    hash_table = {}
    table_file = target_directory.joinpath(table_file_name)
    with table_file.open() as table:
        for line in table:
            hashed_name, file_name = line.rstrip().split('\t', maxsplit=1)
            logger.info('{0} - "{1}"'.format(hashed_name, file_name))
            hash_table[hashed_name] = file_name
    # restore file name
    target_file_list = [
            file for file in target_directory.iterdir()
            if file.name in hash_table]
    for source in target_file_list:
        destination = source.with_name(hash_table[source.name])
        logger.info('rename: "{0}" -> "{1}"'.format(
                source,
                destination))
        source.rename(destination)
