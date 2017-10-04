def clamp(val, low, high):
    return min((max((val, low)), high))


def map(val, ilow, ihigh, olow, ohigh):
    return olow + (ohigh - olow) * (val - ilow) / (ihigh - ilow)
