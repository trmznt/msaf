
from msaf.models import dbsession
from msaf.models.msdb import Sample, Allele, Marker, AlleleSet, EK
from sqlalchemy import and_
from sqlalchemy.orm import aliased


def summarise_allele( sample_ids, marker_id, threshold = 0 ):
    """ sample_idss is a SQLAlchemy query object containing sample_id """

    sample_with_marker = {}
    sample_with_allele = {}

    alleles = {}
    allele_count = 0

    q = dbsession.query( AlleleSet.sample_id, Allele.value, Allele.size, Allele.height ).join(Allele).filter( Allele.marker_id == marker_id ).filter( AlleleSet.sample_id.in_( sample_ids ) ).filter( Allele.type_id.in_([ EK._id('peak-called'), EK._id('peak-bin') ]) )

    # gather relevant data
    for sample_id, value, size, height in q:

        if sample_id not in sample_with_marker:
            sample_with_marker[sample_id] = True

        if height > threshold:
            try:
                sample_with_allele[sample_id] += 1
            except KeyError:
                sample_with_allele[sample_id] = 1

            try:
                alleles[value].append( (size, height) )
            except KeyError:
                alleles[value] = [ (size, height) ]

            allele_count += 1


    # calculate the data
    res = {}
    res['alleles'] = []

    values = list(alleles.keys())
    values.sort()
    for v in values:
        allele = alleles[v]
        n = len(allele)
        f = 1.0 * n/allele_count
        avg_height = sum( [ x[1] for x in allele ] ) / n
        sizes = [ x[0] for x in allele ]
        min_size = min(sizes)
        max_size = max(sizes)
        delta_size = max_size - min_size
        res['alleles'].append( (v, f, n, avg_height, min_size, max_size, delta_size ) )

    res['total_alleles'] = allele_count
    res['samples_count'] = len(sample_with_marker)
    res['samples_allele_count'] = len(sample_with_allele)
    res['marker'] = Marker.get(marker_id).code

    if not res['alleles']:
        res['He'] = 0
        res['delta_status'] = []
        return res

    delta_status = []
    if res['alleles'][1][0] - res['alleles'][0][0] == 1:
        delta_status.append( False )
    else:
        delta_status.append( True )
    for i in range(1, len(res['alleles']) - 1):
        if (    res['alleles'][i][0] - res['alleles'][i-1][0] == 1 or
                res['alleles'][i+1][0] - res['alleles'][i][0] == 1 ):
            delta_status.append( False )
        else:
            delta_status.append( True )
    if res['alleles'][-2][0] - res['alleles'][-1][0] == 1:
        delta_status.append( False )
    else:
        delta_status.append( True )
    res['delta_status'] = delta_status

    n = len(sample_with_allele)
    res['He'] = 1.0 * n / (n - 1) * (1 - sum( [ x[1]**2 for x in res['alleles'] ] ) )

    return res


def summarize_all_alleles( subsets, marker_ids, threshold = 0 ):

    pass


def dominant_genotype( sample_ids, marker_ids, threshold = 0 ):
    """ return dominant genotype for each sample """

    # select t1.sample_id, t1.markerset_id, t1.value, t1.height from alleles as t1
    # left outer join alleles as t2 on (t1.marker_id = t2.marker_id and t1.height < t2.height)
    # where t2.marker_id is null and
    # t1.markerset_id in (4,5,6) and t1.sample_id in (3,4,5,6,7,8,9,10)
    # order by t1.sample_id;


    t1 = aliased( Allele )
    t2 = aliased( Allele )
    marker_ids = [ int(x) for x in marker_ids ]

    q = dbsession.query( t1.sample_id, t1.marker_id, t1.value, t1.height ).\
        outerjoin( t2, and_( t1.marker_id == t2.marker_id, t1.height < t2.height) ).\
        filter( t2.marker_id == None ).order_by( t1.sample_id, t1.marker_id ).\
        filter( t1.sample_id.in_( sample_ids ) ).filter( t1.markerset_id.in_( marker_ids ))

    samples = {}
    
    i = 0
    idx = {}
    for ids in markerset_ids:
        idx[ids] = i
        i += 1

    for sample_id, markerset_id, value, height in q:
        try:
            samples[sample_id][idx[markerset_id]] = value
        except KeyError:
            samples[sample_id] = [0] * len(idx)
            samples[sample_id][idx[markerset_id]] = value

    for k in samples:
        samples[k] = tuple( samples[k] )

    return samples



