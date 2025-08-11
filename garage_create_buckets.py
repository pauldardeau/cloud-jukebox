import os


def run_system_command(cmd):
    print("running command: '%s'" % cmd)
    rc = os.system(cmd)
    print("rc = %d" % rc)
    return rc


def grant_access_to_bucket_for_key(bucket_name, garage_app_key):
    cmd = "garage bucket allow --read --write --owner %s --key %s" % (bucket_name, garage_app_key)
    run_system_command(cmd)


def create_bucket(bucket_name):
    cmd = "garage bucket create %s" % bucket_name
    run_system_command(cmd)


def main(garage_app_key):
    bucket_names = []

    letters = 'abcdefghijklmnopqrstuvwxyz'
    digits = '0123456789'

    bucket_names.append('music-metadata')

    for letter in letters:
        bucket_name = "%s-artist-songs" % letter
        bucket_names.append(bucket_name)

    for digit in digits:
        bucket_name = "%s-artist-songs" % digit
        bucket_names.append(bucket_name)

    for bucket_name in bucket_names:
        create_bucket(bucket_name)

    for bucket_name in bucket_names:
        grant_access_to_bucket_for_key(bucket_name, garage_app_key)


if __name__=='__main__':
    main("app-key-name")

