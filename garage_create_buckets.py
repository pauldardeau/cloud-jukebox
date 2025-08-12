import os
import subprocess


def run_command(command):
    p = subprocess.run(command,
                       shell=True,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    exit_code = p.returncode
    stdout = p.stdout.decode("utf-8")
    stderr = p.stderr.decode("utf-8")
    return exit_code, stdout, stderr


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
    rc, _, _ = run_command(cmd)
    return rc == 0


def bucket_exists(bucket_name):
    cmd = "garage bucket info %s" % bucket_name
    rc, _, _ = run_command(cmd)
    return rc == 0


def main(garage_app_key):
    bucket_names = []
    created_buckets = []

    letters = 'abcdefghijklmnopqrstuvwxyz'
    digits = '0123456789'

    bucket_names.append('music-metadata')
    bucket_names.append('albums')
    bucket_names.append('album-art')
    bucket_names.append('playlists')

    for letter in letters:
        bucket_name = "%s-artist-songs" % letter
        bucket_names.append(bucket_name)

    for digit in digits:
        bucket_name = "%s-artist-songs" % digit
        bucket_names.append(bucket_name)

    for bucket_name in bucket_names:
        if not bucket_exists(bucket_name):
            if create_bucket(bucket_name):
                created_buckets.append(bucket_name)

    for bucket_name in created_buckets:
        grant_access_to_bucket_for_key(bucket_name, garage_app_key)


if __name__=='__main__':
    main("app-key-name")

