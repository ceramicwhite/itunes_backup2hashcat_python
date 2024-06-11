import os
import struct
import re

MAX_PLIST_SEARCH_DISTANCE = 256

def read_plist_file(file_name):
    try:
        with open(file_name, 'rb') as f:
            return f.read()
    except IOError:
        print(f"Could not open file '{file_name}'.")
        return b""

def parse_manifest_file(data):
    wpky = salt = iter_val = dpic = dpsl = None

    data_len = len(data)

    if data_len < 24:
        return None, None, None, None, None

    salt_matches = [m.start() for m in re.finditer(b'SALT....', data)]

    idx_glob = 0
    for _ in range(len(salt_matches)):
        idx_salt = data.find(b'SALT', idx_glob)
        if idx_salt == -1:
            break

        idx_iter = data.find(b'ITER', idx_salt + 1)
        if idx_iter == -1:
            break

        idx_wpky = data.find(b'WPKY', idx_iter + 1)
        if idx_wpky == -1:
            break

        if data_len - idx_wpky < 8:
            break

        if idx_wpky - idx_salt < MAX_PLIST_SEARCH_DISTANCE:
            salt_len = struct.unpack('>L', data[idx_salt + 4:idx_salt + 8])[0]
            iter_len = struct.unpack('>L', data[idx_iter + 4:idx_iter + 8])[0]
            wpky_len = struct.unpack('>L', data[idx_wpky + 4:idx_wpky + 8])[0]

            salt = data[idx_salt + 8:idx_salt + 8 + salt_len]
            iter_val = struct.unpack('>L', data[idx_iter + 8:idx_iter + 8 + iter_len])[0]
            wpky = data[idx_wpky + 8:idx_wpky + 8 + wpky_len]

            break

        idx_glob = idx_wpky + 1

    dpsl_matches = [m.start() for m in re.finditer(b'DPSL....', data)]
    idx_glob = 0
    for _ in range(len(dpsl_matches)):
        idx_dpic = data.find(b'DPIC', idx_glob)
        if idx_dpic == -1:
            break

        idx_dpsl = data.find(b'DPSL', idx_dpic + 1)
        if idx_dpsl == -1:
            break

        if idx_dpsl - idx_dpic < MAX_PLIST_SEARCH_DISTANCE:
            dpic_len = struct.unpack('>L', data[idx_dpic + 4:idx_dpic + 8])[0]
            dpsl_len = struct.unpack('>L', data[idx_dpsl + 4:idx_dpsl + 8])[0]

            dpic = struct.unpack('>L', data[idx_dpic + 8:idx_dpic + 8 + dpic_len])[0]
            dpsl = data[idx_dpsl + 8:idx_dpsl + 8 + dpsl_len]

            break

        idx_glob = idx_dpsl + 1

    return wpky, salt, iter_val, dpic, dpsl

def itunes_plist_get_hash(file_name):
    file_content = read_plist_file(file_name)

    if len(file_content) > 0:
        wpky, salt, iter_val, dpic, dpsl = parse_manifest_file(file_content)

        if not wpky or not salt or not iter_val:
            print(f"ERROR: Missing components in '{file_name}'")
            return ""

        if len(wpky) != 40 or len(salt) != 20:
            print(f"ERROR: Incorrect lengths in '{file_name}'")
            return ""

        if dpsl:
            if dpic < 1 or len(dpsl) != 20:
                print(f"ERROR: Invalid DPIC/DPSL in '{file_name}'")
                return ""
            return f"$itunes_backup$*10*{wpky.hex()}*{iter_val}*{salt.hex()}*{dpic}*{dpsl.hex()}"
        else:
            return f"$itunes_backup$*9*{wpky.hex()}*{iter_val}*{salt.hex()}**"

    return ""

def usage(program_name):
    print(f"Usage: {program_name} <Manifest.plist file>...")

def main():
    import sys

    if len(sys.argv) < 2:
        usage(sys.argv[0])
        sys.exit(1)

    file_list = sys.argv[1:]

    for file_name in file_list:
        if not os.path.exists(file_name):
            print(f"WARNING: could not open file '{file_name}'")
            continue

        hash_buf = itunes_plist_get_hash(file_name)
        if hash_buf:
            print(hash_buf)

if __name__ == "__main__":
    main()
