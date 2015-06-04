
import numpy as np
from scipy.signal import find_peaks_cwt
from scipy.optimize import curve_fit
from matplotlib import pyplot as pt
import pprint



ladders = {
    'LIZ500': [ 35, 50, 75, 100, 139, 150, 160, 200, 250, 300, 340, 350, 400, 450, 490, 500 ],
    'ROX500': [ 35, 50, 75, 100, 139, 150, 160, 200, 250, 300, 340, 350, 400, 450, 490, 500 ],
    'LIZ600': [ 20, 40, 60, 80, 100, 114, 120, 140, 160, 180, 200, 214, 220, 240, 250, 260, 280, 300, 314, 320, 340, 360, 380, 400, 414, 420, 440, 460, 480, 500, 514, 520, 540, 560, 580, 600 ],
}

def plot_peaks(peaks, symbol = 'ro'):
    for (x,y) in peaks:
        pt.plot(x, y, symbol)


def find_peaks( signal, min_height = 25, min_peak_ratio = 0.5, max_peak_ratio = 7, ladder=False ):
    """ find peaks in the signal spectrum
        return [ (indice, height), ... ]
        we differentiate settings between ladder (since we know the absolute size of
        the peaks) and the sample
    """

    if ladder:
        widths = np.arange(5,15)
    else:
        widths = np.arange(5,15)

    #peak_index = find_peaks_cwt( signal, widths, min_snr = 1, min_length = 1, max_distances = widths/23, noise_perc = 25, gap_thresh = 50 )

    peak_index = find_peaks_cwt( signal, widths )

    if not peak_index:
        return []

    peaks = [ ( x, signal[x] ) for x in peak_index ]
    print("initial peaks: %d" % len(peaks))
    pt.plot( signal )
    plot_peaks( peaks, 'ro' )
    pt.show()
    pt.close()


    # filter for min_height
    peaks = [ peak for peak in peaks if peak[1] > min_height ]
    pt.plot( signal )
    plot_peaks( peaks, 'ro' )
    pt.show()
    pt.close()


    if not peaks:
        return []

    heights = [ peak[1] for peak in peaks ]

    # filter for maximum peak ratio with 75th percentile
    upper_percentile = np.percentile( heights, 75 )
    max_height = upper_percentile * max_peak_ratio
    print("heights:")
    print(heights)
    print("upper_percentile:", upper_percentile)
    print("max_height:", max_height)
    peaks = [ peak for peak in peaks if peak[1] < max_height ]
    pt.plot( signal )
    plot_peaks( peaks, 'ro' )
    pt.show()
    pt.close()


    return peaks


def fit_standard( x, y, order = 3 ):
    """ fit x & y
        return ( z, p, rss )
    """

    z = np.polyfit(x, y, order )
    p = np.poly1d( z )

    y_p = p(x)
    rss = ( (y_p - y) ** 2 ).sum()

    return z, p, rss


def sort_nearest_y( y, values ):
    d = [ ((y - v) ** 2, v) for v in values ]
    d.sort()
    return d


def assign_nearest_y( x, y, p ):
    """ assign each value in x to the nearest y based of p function,
        without dropping any x
        returns new_x, new_y
    """

    x.sort( reverse=True )
    y.sort( reverse=True )
    #print("initial x & y")
    #print(x)
    #print(y)
    
    assigned_y = {}
    for i in x:
        y_p = p(i)
        closest_y = sort_nearest_y( y_p, y )
        if closest_y[0][1] not in assigned_y:
            assigned_y[ closest_y[0][1] ] = (i, closest_y)
        else:
            x2, closest_y2 = assigned_y[ closest_y[0][1] ]
            if closest_y2[0][0] > closest_y[0][0]:
                assigned_y[ closest_y[0][1] ] = (i, closest_y)
                assigned_y[ closest_y2[1][1] ] = (x2, closest_y2[1:])
    results = [ (k, assigned_y[k][0]) for k in assigned_y ]
    results.sort()
    #pprint.pprint( [ (k,assigned_y[k]) for k in reversed(sorted(assigned_y.keys())) ] )
    #print("alignment")
    #print(results)
    return [ e[1] for e in results ], [ e[0] for e in results ]


def assign_nearest_y( x, y, p ):
    """ assign each x to the nearest y based on p function, without dropping any x
        return aligned_x, aligned_y
    """

    assigned_y = {}

    # cluster all x into corresponding y
    for i in x:
        y_p = p(i)
        distances = sort_nearest_y( y_p, y )
        if not distances[0][1] in assigned_y:
            assigned_y[ distances[0][1] ] = [ (i, distances) ]
        else:
            assigned_y[ distances[0][1] ].append( (i, distances) )

    #


def fit_ladder_peaks( peaks, ladder ):
    """ assign each peaks to each value in ladder and estimate Z & RSS
            @peaks = list ~ [ ( peak_x, peak_height ), ... ]
            @ladder = [ 100, 200, 300, ... ]
        returning ([ (value, size, peak, height, area), ... ], Z, RSS )
    """

    # we will iteratively assign the peaks
    # all peaks should be assigned to the ladders, but not vice versa
    # eg. some ladders might be missing some peaks

    # initial peak assignment: assign the lattest peak to the lattest ladder

    indices = [ e[0] for e in peaks]
    min_len = min( len(indices), len(ladder) )
    fitted_indices = indices[:min_len]
    fitted_ladder = ladder[:min_len]
    z, p, rss = fit_standard( fitted_indices, fitted_ladder )
    return z, p, rss, fitted_indices, fitted_ladder

    print('initial rss: %5.3f' % rss)
    pt.plot( fitted_indices, fitted_ladder, 'ro' )
    x0 = np.arange(min(fitted_indices),max(fitted_indices))
    y0 = p(x0)
    pt.plot(x0, y0)
    pt.show()

    iteration = 0
    while True:
        
        # reassign x to the nearest ladder
        iteration += 1
        curr_fitted_ladder, curr_fitted_indices = assign_nearest_y(ladder, indices, p )
        curr_z, curr_p, curr_rss = fit_standard( curr_fitted_ladder, curr_fitted_indices )
        print('Iter: %d, rss: %5.3f' % (iteration, curr_rss))

        if (curr_rss >= rss and len(fitted_indices) >= (len(indices) - 2)) or iteration > 10:
            return z, p, rss, fitted_indices, fitted_ladder

        z, p, rss = curr_z, curr_p, curr_rss
        fitted_indices, fitted_ladder = curr_fitted_indices, curr_fitted_ladder

    raise RuntimeError('FATAL ERROR')


def find_ladder_peaks( signal, ladder ):
    """ return z, p, rss, indices, ladder """

    result = None
    peaks = list(reversed(find_peaks( signal, ladder=True )))
    ladder = list(reversed(ladder))
    n = len(ladder)

    pt.plot( signal )
    plot_peaks( peaks, 'ro' )
    pt.show()
    pt.close()

    for i in range(5):
        curr_result = fit_ladder_peaks( peaks, ladder[i:] )
        # check rss
        if not result:
            result = curr_result
        elif result[2] > curr_result[2]:
            result = curr_result

    return result


def gauss(x, *p):
    A, mu, sigma = p
    return A * np.exp( -(x-mu)**2 / (2.*sigma**2) )


def gauss_func(x, a, x0, sigma):
    return a*np.exp(-(x-x0)**2/(2*sigma**2))


def gauss_fit( signal, a0, x0, sigma = 1 ):
    """ return sigma, area and width """
    x = range(signal)
    popt, pcov = curve_fit(gauss_func, x, signal, p0 = (a0, x0, sigma))

    return popt, pcov


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

    ladder = find_ladder_peaks( channel.raw, ladders['LIZ500'] )
    heights = [ channel.raw[i] for i in ladder[3] ]
    pt.plot( channel.raw, color = rgb )
    pt.plot( ladder[3], heights, 'ro' )
    for (x,y,t) in zip(ladder[3], heights, ladder[4]):
        pt.text(x,y,str(t), fontsize=12)

    pt.xlim(1000, 10000)
    pt.ylim(-5, max( heights ) + 100 )

    pt.show()
    #pt.savefig( sys.argv[1] + '.ladder.pdf' )

    return

    for name in channels:

        if name == 'LIZ':
            continue

        channel = channels[name]
        rgb = np.array(wavelen2rgb( channel.wavelength, 100 )) / 100
        pt.plot( channel.raw, color = rgb )

        peaks = find_peaks( channel.raw, max_peak_ratio = 100 )
        print( name )
        print( peaks )
        pt.plot( [ e[0] for e in peaks ], [ e[1] for e in peaks ], 'b^' )
        for (x,y) in peaks:
            pt.text(x, y+10, "%3.1f" % ladder[1](x), fontsize=12)

    pt.xlim(1000,10000)
    pt.ylim(-5, 2500)
    pt.savefig( sys.argv[1] + '.pdf' )


if __name__ == '__main__':
    test()
