"""Conservative private input file RAM reservation inside the unchanged8GiB budget."""
import stat

MIB = 1024 ** 2
LIMIT = 256 * MIB


def reserve_private_inputs(allocations, source, key):
    total = 0
    for path, maximum in ((source, LIMIT), (key, 32)):
        if path is None:
            continue
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or not 0 < info.st_size <= maximum:
            raise ValueError('Baseline input must be regular, private and within its declared bound')
        if path == key and info.st_size != 32:
            raise ValueError('Baseline key must contain32 bytes')
        total += info.st_size
    reserved = (total + MIB - 1) // MIB
    result = dict(allocations)
    cpu, memory = result['app']
    if memory - reserved < 1024:
        raise ValueError('Baseline reservation would leave less than1GiB app memory')
    result['app'] = cpu, memory - reserved
    if sum(value[1] for value in result.values()) + 128 + reserved != 8192:
        raise ValueError('Baseline input and kernel ceilings must total8GiB')
    return result, reserved
