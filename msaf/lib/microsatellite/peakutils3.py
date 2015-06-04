import numpy as np
from scipy.signal import find_peaks_cwt
from scipy.optimize import curve_fit, leastsq
from scipy.interpolate import UnivariateSpline
from matplotlib import pyplot as pt
from .traceutils import smooth_signal
from operator import itemgetter
from bisect import bisect_left

import pprint


ladders = {
    'LIZ500': [ 35, 50, 75, 100, 139, 150, 160, 200, 250, 300, 340, 350, 400, 450, 490, 500 ],
    'ROX500': [ 35, 50, 75, 100, 139, 150, 160, 200, 250, 300, 340, 350, 400, 450, 490, 500 ],
    'LIZ600': [ 20, 40, 60, 80, 100, 114, 120, 140, 160, 180, 200, 214, 220, 240, 250, 260, 280, 300, 314, 320, 340, 360, 380, 400, 414, 420, 440, 460, 480, 500, 514, 520, 540, 560, 580, 600 ],
}


class Peak(object):

    """ follow the structure of msaf Allele database schema
    """

    def __init__(self, value=-1, size=-1, peak=-1, height=-1, area=-1, delta=0,
                    type=None, method=None, marker=None):
        self.value = value
        self.size = size
        self.peak = peak
        self.height = height
        self.area = area
        self.delta = delta
        self.type = type
        self.method = method
        self.marker = marker


def calculate_area(y, p, threshold):

        area = 0
        x = p + 1
        h = y[x]
        while h > threshold:
            area += h
            x = x + 1
            if x >= len(y):
                break
            h = y[x]

        x = p - 1
        h = y[x]
        while h > threshold:
            area += h
            x = x - 1
            if x < 0:
                break
            h = y[x]

        area += y[ p ]
        
        return area


def find_peaks( signal, min_height = 15, relative_min = 0, relative_max = 0, ssignal = None ):
    """ find peaks from x with min_height, filtered by relative_min and
        relative_max from median height.
        returns [ (peak, height, area), ... ]

    """

    widths = np.arange(5, 15)

    indices = find_peaks_cwt( signal, widths )

    if not indices:
        return []

    raw_peaks = []
    for idx in indices:
        height = signal[idx]
        if height < min_height:
            continue
        raw_peaks.append( (idx, height) )

    if relative_min > 0 or relative_max > 0:
        med = np.median( list(p[1] for p in raw_peaks) )
        if relative_min > 0:
            median_min = med * relative_min
            raw_peaks = [ p for p in raw_peaks if p[1] > median_min ]
        if relative_max > 0:
            median_max = med * relative_max
            raw_peaks = [ p for p in raw_peaks if p[1] < median_max ]


    #pprint.pprint(raw_peaks)
    # find the area

    if ssignal is None:
        ssignal = smooth_signal( signal )

    # calculate area

    threshold = np.percentile( ssignal, 75 )
    peaks = []
    for (peak, height) in raw_peaks:
        peaks.append( (peak, height, calculate_area( ssignal, peak, threshold )) )

    return peaks

    # this part is not used anymore (or yet)

    peaks = []
    half_width = 150
    x = np.arange(half_width * 2)
    for (peak, height) in raw_peaks:
        if peak < half_width:
            offset = 0
        elif peak + half_width > len(ssignal):
            offset = len(ssignal) - half_width * 2
        else:
            offset = peak - half_width
        o_peak = peak - offset
        params = ( height, o_peak, 5 )
        results, value = leastsq(err, params, args=(x, ssignal[offset:offset + 2*half_width]))
        peaks.append( (offset + results[1], results[0], results[2]) )
    
    #pprint.pprint(peaks)
    return peaks
        

    #x = np.arange(len(ssignal))
    #pprint.pprint(params)
    #results, value = leastsq(err, params, args=(x, ssignal))

    #return results.reshape(-1, 3)


def find_ladder_peaks( signal, ladder, ssignal = None, min_height = 30, relative_min = 0.50,
                        relative_max = 4 ):
    """ returns ([ (value, size, peak, height, sigma), ...], Z, RSS )
    """

    ladder_peaks = find_peaks( signal, min_height = min_height, relative_min = relative_min,
                                relative_max = relative_max, ssignal = ssignal)
    ladder_peaks.reverse()
    ladder = list(reversed(ladder))

    new_ladder_peaks = []

    idx = 0
    while idx < len(ladder_peaks) - 1:
        if ladder_peaks[idx][0] - ladder_peaks[idx+1][0] > 100: # minimum time separation
            new_ladder_peaks.append( ladder_peaks[idx] )
        else:
            if ladder_peaks[idx][1] > ladder_peaks[idx+1][1]:
                new_ladder_peaks.append( ladder_peaks[idx] )
            else:
                new_ladder_peaks.append( ladder_peaks[idx+1] )
                idx += 1
        idx += 1

    ladder_peaks = new_ladder_peaks

    # assumptions:
    # - no drop peaks
    # - the maximum number of missing peaks at the later retention time is 5 (shifted out)
    adaptive_results = []
    for i in range(5):
            result_peaks = [ (s, s, x[0], x[1], x[2])
                                for (s,x) in zip(ladder[i:], ladder_peaks) ]
            ds_peaks = [ (-1, -1, x[0], x[1], x[2])
                                for x in ladder_peaks[ len(ladder) - i: ] ]
            result_peaks.reverse()
            ds_peaks.reverse()

            x, y = [], []
            for v, s, p, h, a in result_peaks:
                x.append( p )
                y.append( s )

            z = np.polyfit( x, y, 3 )
            p = np.poly1d( z )
            y_p = p(x)
            rss = ( (y_p - y) ** 2 ).sum()

            # for now, discard the unused (or noise) peaks as -1 will be duplicated
            # within alleleset
            adaptive_results.append( (result_peaks, z, rss) )

    adaptive_results.sort( key = itemgetter(2) )

    return adaptive_results

def least_square( z ):
    """ 3rd order polynomial resolver
    """
    return np.poly1d( z )

def cubic_spline( x, y ):
    """ cubic spline interpolation
        x is peaks, y is standard size
    """
    return UnivariateSpline(x, y, s=3)


def filter_estimate_peaks( peaks, z, min_size = 100, min_height=15 ):
    """ filter peaks after being estimated for the size and value
        peaks = [ (peak, height, area), ... ]
        z = z-value from ladder
        returning [ (value, size, peak, height, area), ... ]
    """
    d = {}
    f = np.poly1d( z )
    for (p, h, a) in peaks:
        size = float( f(p) )
        value = int(round(size))
        area = int(a)
        height = float(h)
        if height < min_height or size < min_size:
            # discard any peak with height below min_height and size below min_size
            continue
        if value not in d or d[value][3] < height:
            # if value is not in d, or if value in d has lower peak
            d[value] = ( value, size, p, height, area )

    # return by sorting based on value
    return sorted(d.values())

def call_peaks( peaks, func, min_size=100, min_height=15 ):

    d = {}
    for (p, h, a) in peaks:
        size = float( func(p) )
        value = round(size)
        area = int(a)
        height = float(h)
        if height < min_height or size < min_size:
            # discard any peak with height below min_height and size below min_size
            continue
        if value not in d or d[value][3] < height:
            # if value is not in d, or if value in d has lower peak
            d[value] = ( value, size, p, height, area )

    # return by sorting based on value
    return sorted(d.values())



def analyze_peaks( peaks, defined_marker, undefined_marker, min_size, max_size = 0, stutter_size=1.25, method='allele-cubicspline' ):
    """ return [ (value, size, peak, height, area, peak_type, peak_marker, peak_method'), ... ]
    """

    filtered_peaks = []
    for idx in range(len(peaks)):
        
        (v, s, p, h, a) = peaks[idx]
        if v < min_size and s < min_size:
            filtered_peaks.append( (v, s, p, h, a, 'peak-unassigned', undefined_marker,
                method) )
            continue

        if max_size > 0 and v > max_size and s > max_size:
            filtered_peaks.append( (v, s, p, h, a, 'peak-unassigned', undefined_marker,
                method) )
            continue

        type = 'peak-called'
        if idx > 0:
            (v0, s0, p0, h0, a0) = peaks[idx-1]
            if s - s0 < stutter_size:
                type = 'peak-stutter' if h0 > h else 'peak-called'
        if idx < len(peaks) - 1:
            (v1, s1, p1, h1, a1) = peaks[idx+1]
            if s1 - s < stutter_size:
                type = 'peak-stutter' if h1 > h else 'peak-called'

        filtered_peaks.append( (v, s, p, h, a, type, defined_marker, method) )

    return filtered_peaks


def check_overlap_peaks( peaks_list, threshold = 1.25):
    """ check and changes peak_type from peak-size to peak-overlap as necessary
    """

    for i,peaks in enumerate(peaks_list):
        for j in range(len(peaks)):
            val, size, peak, height, area, peak_type, marker, method = peaks[j]
            if peak_type != 'peak-called':
                continue
            # only process peak-size type
            for k in range(len(peaks_list)):
                if k == i:
                    continue
                for p in peaks_list[k]:
                    var_r, size_r, peak_r, height_r, area_r, peak_type_r, marker_r, method_r = p
                    if peak_type_r not in ['peak-called', 'peak-bin']:
                        continue
                    if abs(size_r - size) < threshold:
                        if height < height_r:
                            peak_type = 'peak-overlap'

            if peak_type != 'peak-called':
                peaks[j] = (val, size, peak, height, area, peak_type, marker, method)


def bin_peaks( peaks, binlist, threshold=1.5 ):
    """ changes peak value to the nearest bin from binlist and complains if the closer bin
        is above the allowed threshold
        peaks: list of Peak-alike
    """
    
    for peak in peaks:

        if peak.type not in ['peak-called', 'peak-bin']:
            continue

        size = peak.size

        pos = bisect_left( binlist, size )
        if pos == 0:
            value = binlist[0]
        elif pos == len(binlist):
            value = binlist[-1]
        else:
            before = binlist[pos - 1]
            after = binlist[pos]
            if after - size < size - before:
                value = after
            else:
                value = before
        if abs(value - size) > threshold:
            raise RuntimeError('ERR: binned peak with size: %3.2f for value: %3.2f is above range threshold: %2.1f'
                    % (size, value, threshold) )

        peak.value = value
        peak.type = 'peak-bin'


def create_bins(value, interval=3, min_size=200, max_size=400):
    modulo = value % interval
    ceil = int( min_size / interval) + 1
    return list(range(ceil * interval + modulo, max_size, interval))


def gaussian(x, A, x0, sig):
    return A*np.exp(-(x-x0)**2/(2.0*sig**2))

def fit(p,x):
    return np.sum([gaussian(x, p[i*3],p[i*3+1],p[i*3+2]) 
                   for i in range(int(len(p)/3))],axis=0)

err = lambda p, x, y: fit(p,x)-y


def test():


    import sys
    import traceio
    from matplotlib import pyplot as pt
    from wavelen2rgb import wavelen2rgb

    with open( sys.argv[1], 'rb' ) as f:
        t = traceio.read_abif_stream( f )

    channels = t.get_channels()

    # get ladder first

    channel = channels['LIZ']
    rgb = np.array(wavelen2rgb( channel.wavelength, 100 )) / 100
    pt.plot( channel.raw, color = rgb )

    #peaks = find_peaks( channel.raw, relative_min = 0.3, relative_max = 3 )
    (peaks, z, rss) = find_ladder_peaks( channel.raw, ladders['LIZ500'] )[0]
    #heights = [ channel.raw[i] for i in ladder[3] ]
    pt.plot( channel.raw, color = rgb )
    indices = [ p[2] for p in peaks ]
    heights = [ p[3] for p in peaks ]
    sizes = [ p[1] for p in peaks ]
    pt.plot( indices, heights, 'ro' )
    for (x,y,t) in zip(indices, heights, sizes):
        pt.text(x,y,str(int(round(t))), fontsize=12)

    pt.xlim(0, 10000)
    pt.ylim(-5, max( heights ) + 100 )

    pt.show()



if __name__ == '__main__':
    test()
