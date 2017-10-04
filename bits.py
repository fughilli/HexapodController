def make_mask(width):
    return (1 << width) - 1

def make_field(val, offset, width):
    return (make_mask(width) & val) << offset

def get_field(val, offset, width):
    return (make_mask(width) & (val >> offset))
