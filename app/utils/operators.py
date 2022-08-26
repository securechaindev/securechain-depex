from operator import eq, gt, lt, ge, le, ne


def approx_gt(version, version_) -> bool:
    str_version = str(version)
    str_version_ = str(version_)
    
    match str_version.count('.'):
        case 0:
            str_version += '.0'
        case 1:
            str_version += '.0.0'
        case 2:
            str_version += '.0.0.0'

    parts = str_version.split('.')
    parts_ = str_version_.split('.')
    tam_ = len(parts_) - 1

    return version >= version_ and parts[tam_] >= parts_[tam_]

def approx_gt_patch(version, version_) -> bool:
    str_version = str(version)
    str_version_ = str(version_)

    parts = str_version.split('.')
    parts_ = str_version_.split('.')

    return version >= version_ and parts[2] >= parts_[2]

def approx_gt_minor(version, version_) -> bool:
    str_version = str(version)
    str_version_ = str(version_)

    parts = str_version.split('.')
    parts_ = str_version_.split('.')

    return version >= version_ and parts[1] >= parts_[1]


ops = {
    '=': eq,
    '==': eq,
    '>': gt,
    '<': lt,
    '>=': ge,
    '<=': le,
    '!=': ne,
    '~>': approx_gt,
    '~=': approx_gt,
    '^': approx_gt_minor,
    '~': approx_gt_patch
}