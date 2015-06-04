
from msaf.models import dbsession
from msaf.models.msdb import Sample, Allele, AlleleSet
from sqlalchemy import func
import numpy


def mean_moi(sample_ids, marker_ids, threshold=0):

    sample_moi = {}

    for marker_id in marker_ids:

        q = dbsession.query( AlleleSet.sample_id, func.count(Allele.value) ).join(Allele).\
            group_by( AlleleSet.sample_id ).filter( Allele.marker_id == marker_id ).\
            filter( Allele.height > threshold ).\
            filter( AlleleSet.sample_id.in_( sample_ids ) )

        for sample_id, moi in q:
            try:
                sample_moi[sample_id].append( moi )
            except KeyError:
                sample_moi[sample_id] = [ moi ]


    total_moi = 0
    loci_dist = [0] * (len(marker_ids) + 1)
    mois = []
    moi_dist = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0 }
    

    for allele_count in sample_moi.values():
        moi = max( allele_count )
        total_moi += moi
        mois.append(moi)
        moi_dist[moi] += 1

        if moi > 1:
            n = len( list(filter( lambda x: x > 1, allele_count )) )
            loci_dist[n] += 1

    # normalise dist_moi
    #n = sum( dist_moi )
    #for i in range(len(dist_moi)):
    #    dist_moi[i] = 1.0 * dist_moi[i] / n


    moi_list = numpy.array( mois )

    res = {}
    res['median'] = numpy.median( moi_list )
    res['mean'] = 1.0 * total_moi / len(sample_moi)
    res['sample_size'] = len(sample_moi)
    res['loci_distribution'] = loci_dist
    res['moi_distribution'] = moi_dist

    return res


def loci_distribution(sample_ids, markerset_ids, threshold=0):
    pass
    
