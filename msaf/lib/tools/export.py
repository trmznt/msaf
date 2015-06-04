
import yaml

from io import BytesIO, StringIO
from pandas import concat

from msaf.models import *

from msaf.lib.tools.genotype import dominant_genotypes
from msaf.lib.querycmd import parse_querycmd
from msaf.lib.queryfuncs import AlleleDF

from msaf.lib.analytics import get_genotypes


def export_genotypes( sample_ids, threshold, marker_ids  ):

    genotypes = dominant_genotypes( sample_ids, threshold, marker_ids)

    return export_flat( genotypes )


def export_flat( genotypes ):

    ostr = BytesIO()

    for g in genotypes.itertuples():
        ostr.write( (' '.join( str(int(x)) for x in g ) + '\n').encode('ASCII') )

    ostr.seek(0)
    return ostr


def export_allele( sample_ids ):

    samples = {}
    
    q = Sample.query().filter( Sample.id.in_( sample_ids ) )

    for s in q:
        allele_list = {}
        alleles = s.get_alleles()
        for a in alleles:
            marker_code = a.marker.code
            if marker_code in allele_list:
                allele_list[marker_code].append( (a.value, a.size. a.height) )
            else:
                allele_list[marker_code] = [ (a.value, a.size, a.height) ]
        samples[s.code] = allele_list

    ostr = BytesIO()

    ostr.write( yaml.dump( samples, default_flow_style = False ) )
    ostr.seek( 0 )
    return ostr


def export_data( queryset, threshold, marker_ids, fmt ):

    sample_ids = parse_querycmd( queryset )

    if fmt.upper() == 'FLAT':
        # FLAT file, LIAN 3.5
        return export_genotypes( sample_ids, threshold, marker_ids )
    elif fmt.upper() == 'YAML-ALLELE':
        return export_allele( sample_ids )

    raise RuntimeError('should not be here!')


def export_arlequin( genotype_sets, recode = False ):
    """ recode ~ whether to use allele-specific population
        return (buffer, used_sets )
    """

    _ = [   '[Profile]',
            '  Title="MsAF exported data"',
            '  NbSamples=%d' % len(genotype_sets),
            '  DataType=MICROSAT',
            '  GenotypicData=0',
            '  GameticPhase=0',
            '  MissingData="?"',
            '  LocusSeparator=WHITESPACE',
            '',
    ]

    _ += [  '[Data]',
            '  [[Samples]]',
    ]

    used_sets = []
    counter = 0

    for (idx, (genotype_set, genotypes)) in enumerate(get_genotypes(genotype_sets)):

        _ += [  '    SampleName="%s"' % genotype_set.get_label(),
                '    SampleSize=%d' % len(genotypes),
                '    SampleData={',
        ]
        for e in genotypes.itertuples():
            if recode:
                counter += 1
                _.append( '    %d 1 ' % counter + ' '.join( '%02d%03d' % (idx,x) for x in e[1:] ) )
            else:
                _.append( '    %d 1 ' % e[0] + ' '.join( str(int(x)) for x in e[1:] ) )

        _.append('    }')
        used_sets.append( genotype_set )

    ostr = StringIO()
    ostr.write( '\n'.join( _ ) )
    ostr.seek(0)

    return (ostr, used_sets)


def export_structure( genotype_sets ):
    """ return (buffer_data, buffer_params)
        LABEL=1, MARKERNAMES=1, POPDATA=1, NUMINDS=?, NUMLOCI=?, MISSING = -9
        POPFLAG=0, LOCDATA=0, PHENOTYPE=0, EXTRACOLS=0, PLOIDY=1
    """

    _ = []

    df_sets = get_genotypes(genotype_sets, dropna = False)
    genotype_df = concat( [ x[1] for x in df_sets],
                            keys = range(len(df_sets)) )
        
    genotype_df = genotype_df.fillna( -9 )
    for e in genotype_df.itertuples():
        _.append( '%s %d ' % (str(e[0][1]), e[0][0]) + ' '.join( str(int(x)) for x in e[1:] ))

    params = [
        '#define MAXPOPS    %d' % len(df_sets),
        '#define BURNIN     10000',
        '#define NUMREPS    20000',
        '#define INFILE     infile',
        '#define OUTFILE    outfile',
        '#define PLOIDY     1',
        '#define NUMINDS    %d' % len(genotype_df),
        '#define NUMLOCI    %d' % len(genotype_df.columns),
        '#define MISSING    -99',
        '#define LABEL      1',
        '#define POPDATA    1',
        '#define POPFLAG    0',
        '#define LOCDATA    0',
        '#define PHENOTYPE  0',
        '#define EXTRACOLS  0',
        '#define MARKERNAMES    0',
    ]
        


    return ('\n'.join( _ ), '\n'.join( params ))


