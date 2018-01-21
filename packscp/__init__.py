# -*- coding: utf-8 -*-


import datetime
import hashlib
import logging
import pathlib
import subprocess


table_file_name = 'hash_table.txt'


def pack(target_list, logger=None):
    # logger
    if logger is None:
        logger = logging.getLogger(__name__)
    logger.info('pack: {0}'.format(', '.join(map(str, target_list))))
    # hashing
    hash_table = {}

    def hashing(target):
        if target.is_dir():
            for child in target.iterdir():
                hashing(child)
        elif target.is_file():
            # hashing
            hashed = hashlib.sha256(target.as_posix().encode())
            logger.info('{0}: "{1}" -> {2}'.format(
                    hashed.name,
                    target.as_posix(),
                    hashed.hexdigest()))
            # duplication check
            if hashed in hash_table:
                logger.error('dupicated: "{0}" -> "{1}"'.format(
                        target.as_posix(),
                        hashed.hexdigest()))
            else:
                hash_table[hashed] = target

    for target in target_list:
        hashing(target)
    # create temp directory
    temp_directory = pathlib.Path(
            datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    logger.info('mkdir {0}'.format(temp_directory))
    temp_directory.mkdir()
    # create hash table
    table_file = temp_directory.joinpath(table_file_name)
    with table_file.open(mode='w', encoding='utf-8') as table:
        for key in sorted(hash_table.keys(), key=lambda x: x.hexdigest()):
            table.write('{0}\t{1}\n'.format(
                    key.hexdigest(),
                    hash_table[key].as_posix()))
    # create symlink
    for hashed, path in hash_table.items():
        temp_directory.joinpath(hashed.hexdigest()).symlink_to(path.resolve())
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


def unpack(target, destination=None, logger=None):
    # logger
    if logger is None:
        logger = logging.getLogger(__name__)
    logger.info('unpack: {0}'.format(target))
    # destination
    if destination is None:
        destination = pathlib.Path()
    # open table
    hash_table = {}
    table_file = target.joinpath(table_file_name)
    with table_file.open(encoding='utf-8') as table:
        for line in table:
            hashed, path = line.rstrip().split('\t', maxsplit=1)
            logger.info('{0} - "{1}"'.format(hashed, path))
            hash_table[hashed] = path
    # rename
    file_list = [
            file for file in target.iterdir()
            if file.is_file() and (file.name in hash_table)]
    for hashed_path in file_list:
        original_path = destination.joinpath(hash_table[hashed_path.name])
        logger.info('rename: "{0}" -> "{1}"'.format(
                hashed_path,
                original_path))
        # mkdir
        if not original_path.parent.exists():
            logger.info('mkdir {0}'.format(original_path.parent))
            original_path.parent.mkdir(parents=True)
        # existance check
        if original_path.exists():
            logger.error('{0} already exists'.format(original_path))
            continue
        else:
            # rename
            hashed_path.rename(original_path)
    # delete target
    if len(list(filter(lambda x: x != table_file, target.iterdir()))) == 0:
        logger.info('delete: {0}'.format(table_file))
        table_file.unlink()
        logger.info('delete: {0}'.format(target))
        target.rmdir()
