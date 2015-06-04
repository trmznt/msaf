
from math import factorial
from .peakdetect import peakdetect
import numpy as np
from operator import itemgetter

def spacing( a ):
    """ return the min and max length between consecutive elements """
    spaces = [ j-i for i,j in zip( a[:-1], a[1:] ) ]
    return min( spaces ), max( spaces )


def polyfit(x, y, order=3):
    z = np.polyfit(x, y, order)
    p = np.poly1d(z)

    y_p = p(x)
    rss = ((y_p - y) ** 2).sum()

    return z, p, rss


def calculate_area( y, peaks ):
    
    # use median as the threshold (or 0)
    threshold = max( np.median( y ), 0 )

    areas = []
    for p in peaks:
        area = 0
        x = p[0] + 1
        h = y[x]
        while h > threshold:
            area += h
            x = x + 1
            if x >= len(y):
                break
            h = y[x]

        x = p[0] - 1
        h = y[x]
        while h > threshold:
            area += h
            x = x - 1
            if x < 0:
                break
            h = y[x]

        area += y[ p[0] ]
        areas.append( area )

    return areas
    

def filter_peaks( f, peaks, areas ):
    d = {}
    for (p, a) in zip( peaks, areas ):
        peak = float(p[0])
        height = float(p[1])
        size = float(f( peak ))
        value = int(round(size, 0))
        a = int(a)
        if height < 0:
            # discard peaks below 0
            continue
        if value not in d:
            d[value] = ( value, size, peak, height, a )
        elif d[value][3] < height:
            # if value already in d, use the highest peak
            d[value] = ( value, size, peak, height, a )

    return sorted(d.values())

def filter_estimate_peaks( peaks, z, min_size = 100, min_height=50 ):
    """ filter peaks after being estimated for the size and value
        peaks = [ (peak, height, area), ... ]
        z = z-value from ladder
        returning [ (value, size, peak, height, area), ... ]
    """
    d = {}
    f = np.poly1d( z )
    for (p, h, a) in peaks:
        size = float( f(p) )
        value = int(round(size, ))
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


def separate_fragments( arrays, std, ladder ):
    """ return a list of allele results """

    # find peaks in standard / ladder, std already in savitzky_golay
    ladder_peaks = find_peaks( std, spacing( ladder )[0] )


def find_peaks( y, min_spacing=1, min_strength=50, min_relative=0, max_relative=0):
    """ find peaks from y with min_spacing and min_strength parameters
        returning [ ( peak, height, area), ... ]
    """
    peaks, _ = peakdetect( y, range( len(y) ), min_spacing, min_strength )
    areas = calculate_area( y, peaks )
    
    results = [ (p[0], p[1], a) for (p,a) in zip( peaks, areas ) ]

    if min_relative > 0 or max_relative > 0:
        heights = [ x[1] for x in results ]
        med = np.median(heights)
        if min_relative > 0:
            min_med = med * min_relative
            results = [ x for x in results if min_med < x[1] ]
        if max_relative > 0:
            max_med = med * max_relative
            results = [ x for x in results if x[1] < max_med ]

    return results


def find_ladder_peaks( data, ladder ):
    """ assign each peaks to each value in ladder and estimate Z & RSS
            @peaks = numpy.array
            @ladder = [ 100, 200, 300, ... ]
        returning ([ (value, size, peak, height, area), ... ], Z, RSS )
    """
    # TODO: create an adaptive peak fitter

    # reverse ladder
    min_spacing = spacing(ladder)[0]
    ladder = list(reversed(ladder))

    # perform iterative assignment for 5 consecutive step
    adaptive_results = []

    for h in range(50, 0, -10):

        ladder_peaks = find_peaks( data, min_spacing, h, 0.33, 3.3 )
        ladder_peaks.reverse()

        for i in range(5):
            # TODO: filter unused peaks
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


def gaussian(x, A, x0, sig):
    return A*exp(-(x-x0)**2/(2.0*sig**2))

def fit(p,x):
    return np.sum([gaussian(x, p[i*3],p[i*3+1],p[i*3+2]) 
                   for i in range(len(p)/3)],axis=0)

err = lambda p, x, y: fit(p,x)-y

#params are our intitial guesses for fitting gaussians, 
#(Amplitude, x value, sigma):
#params = [[50,40,5],[50,110,5],[100,160,5],[100,220,5],
#          [50,250,5],[100,260,5],[100,320,5], [100,400,5],   
#          [30,300,150]]  # this last one is our noise estimate
#params = np.asarray(params).flatten()

#x  = xrange(len(y_vals))
#results, value = leastsq(err, params, args=(x, y_vals))

#for res in results.reshape(-1,3):
#    print("amplitude, position, sigma", res)


