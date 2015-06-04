
from rhombus.lib.utils import random_string
from msaf.configs import get_temp_path
from rhombus.lib.exceptions import SysError
from msaf.models import Sample
from msaf.lib.querycmd import parse_querycmd
from msaf.lib.advquerycmd import parse_advquerycmd
from msaf.lib.tools.summary import generate_comprehensive_summary_2, generate_comprehensive_summary_3
from msaf.lib.tools.distance import nj_distance, nj_tree, plot_pca


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os

from itertools import filterfalse
from subprocess import call

class ReportResult(object):

    def __init__(self):
        self.fullpath = None


def xxx_generate_report(batchcode, querytext, location_level = 4,
            threshold = '100 | 33%', fmt='PDF',
            template_file = None):
    
    report = ReportResult()

    # prepare the query
    fullquery = ''
    if batchcode:
        fullquery += '%s[batch]' % batchcode
    if querytext:
        fullquery += querytext

    if not fullquery:
        raise RuntimeError( 'Please provide batch code or querytext' )

    sample_ids = parse_querycmd( fullquery )

    result = generate_comprehensive_summary( sample_ids, location_level )

    # format the TeX file


    tmp_dir = get_temp_path( random_string(8) )
    os.mkdir( tmp_dir )
    tmp_dir += '/'
    tex_filename = tmp_dir + 'report.tex'

    template = open( template_file ).read()

    template = format_report( template, result, tmp_dir )

    with open(tex_filename, 'w') as f:
        f.write( template )

    if fmt == 'PDF':
        # run pdflatex here
        ok = call([   'pdflatex',
                    '-halt-on-error',
                    '-output-directory', tmp_dir,
                    tex_filename
                ])
        if ok != 0:
            raise SysError('pdflatex returned error code: %d' % ok)
        report.fullpath = tmp_dir + 'report.pdf'
        return report

    raise SysError('should not be here!')


def xxx_format_report( template, data, directory ):
    """ from a latex template file, generate pdflatex
    """

    # format TABLE-SAMPLE-LOCATION-BASELINE
    # data['locations']

    buf = []
    buf.append(
        '\\begin{tabular}{lr}\n\\toprule\nLocation & N\\tabularnewline\n\\midrule'
    )
    for (location, n) in data['basic']['locations'].iteritems():
        buf.append( "%s & %d \\tabularnewline" % (location, n) )
    buf.append('\\bottomrule\n\\end{tabular}')

    template = template.replace('TABLE-SAMPLE-LOCATION-BASELINE',
            '\n'.join( buf ))

    # format TABLE-SAMPLE-YEAR
    # data['years']

    buf = []
    buf.append(
        '\\begin{tabular}{llr}\n\\toprule\nYear & Location & N\\tabularnewline\n\\midrule'
    )
    Y = data['basic']['years']
    current_year = 0
    for (index, n) in Y.itertuples():
        year, location = index
        if year == current_year:
            buf.append( " & %s & %d \\tabularnewline" % (location, n) )
        else:
            current_year = year
            buf.append( "%d & %s & %d \\tabularnewline" % ( year, location, n ) )
    buf.append('\\bottomrule\n\\end{tabular}')

    template = template.replace('TABLE-SAMPLE-YEAR', '\n'.join( buf ))


    # format TABLE-MARKER-QUALITY
    # data['marker_quality']

    buf = []
    buf.append(
        '\\begin{tabular}{lrrc}\n\\toprule\n & \multicolumn{2}{c}{Failed Genotyping} & \\tabularnewline\n\\cmidrule(r){2-3}\nMarker & No. & (\\%) & Included in haplotyping\\tabularnewline\n\\midrule'
    )
    for (code, marker_id, no, prop, state) in data['marker_quality']:
        buf.append('%s & %d & %d \\%% & %s\\tabularnewline' % (
            code, no, prop * 100, 'Yes' if state else 'No' ))
    buf.append('\\bottomrule\n\\end{tabular}')

    #template = template.replace('TABLE-MARKER-QUALITY', '\n'.join( buf ))


    ## format TABLE-SAMPLE-FAILURE-RATE
    ## data['sample_quality']

    buf = []
    buf.append(
        '\\begin{tabular}{lrrrrrrr}\n'
        '\\toprule\n'
        ' & & \\multicolumn{4}{c}{Failed Genotyping} & \\multicolumn{2}{c}{Failed Samples} \\tabularnewline\n'
        '\\cmidrule(r){3-6} \\cmidrule(r){7-8}\n'
        'Location & N & Mean & Median & Min & Max & N & (\\%) \\tabularnewline\n'
        '\\midrule\n'
    )

    for (location, failed_genotypes, failed_samples) in data['sample_quality']:
        buf.append(
            '%s & %d & %3.2f & %d & %d & %d & %d & %d \\%% \\tabularnewline' %
            (location, len(failed_genotypes),
                np.mean(failed_genotypes), np.median(failed_genotypes),
                min(failed_genotypes), max(failed_genotypes),
                failed_samples, round(100.0 * failed_samples/len(failed_genotypes)) )
        )
    buf.append('\\bottomrule\n\\end{tabular}')

    template = template.replace('TABLE-SAMPLE-FAILURE-RATE', '\n'.join( buf ))


    ## format PLOT-SAMPLE-QUALITY
    ## data['sample_quality']

    plot_file = directory + 'boxplot-sample-quality.pdf'
    plt.boxplot( [ e[1] for e in data['sample_quality'] ] )
    plt.xticks( range(1, 1 + len(data['sample_quality'])),
                [ e[0] for e in data['sample_quality'] ],
                rotation = 90 )
    plt.ylabel('Number of failed markers')
    plt.savefig( plot_file )
    plt.close()

    template = template.replace( 'PLOT-SAMPLE-QUALITY',
                include_graphics( plot_file ) )


    ## format TABLE-FILTERED-MARKER-QUALITY
    ## data['marker_quality']

    template = template.replace( 'FILTERED-SAMPLE-SIZE', str( data['filtered_sample_size'] ) )
    template = template.replace( 'SAMPLE-SIZE', str( data['sample_size'] ) )

    buf = []
    buf.append(
        '\\begin{tabular}{lrrc}\n\\toprule\n & \multicolumn{2}{c}{Failed Genotyping} & \\tabularnewline\n\\cmidrule(r){2-3}\nMarker & No. & (\\%) & Included in haplotyping\\tabularnewline\n\\midrule'
    )
    for (code, marker_id, no, prop, state) in data['marker_quality']:
        buf.append('%s & %d & %d \\%% & %s\\tabularnewline' % (
            code, no, prop * 100, 'Yes' if state else 'No' ))
    buf.append('\\bottomrule\n\\end{tabular}')

    template = template.replace('TABLE-FILTERED-MARKER-QUALITY', '\n'.join( buf ))


    ##
    ## Allele frequency piecharts
    ##

    buf = []
    buf.append(
        '\\begin{tabular}{lrrrrrr}\n'
        '\\toprule\n'
        '& & \multicolumn{4}{c}{Alleles per sample} & \\tabularnewline\n'
        '\\cmidrule(r){3-6}\n'
        'Marker & Unique Allele & Mean & Median & Min & Max & Expected He\\tabularnewline\n'
        '\\midrule'
    )

    charts = [ r'\begin{figure}[H]', r'\centering' ]

    colors = cm.Accent( [ x/1000 for x in range(0,1001,125) ] )

    for (m, s) in data['marker_summary']:
        buf.append('%s & %d & %1.2f & %d & %d & %d & %3.2f\\tabularnewline' %
            ( s.marker, s.unique_alleles(), s.aps_mean, s.aps_median, s.aps_min, s.aps_max,
                s.he ))

        # generate chart as well

        chart_file = directory + 'marker-%d-pie.pdf' % m

        plt.pie( [ x[2] for x in s.frequencies ], startangle=90, colors = colors )
        plt.axis('equal')
        plt.savefig(chart_file)
        plt.close()

        charts.extend( [ 
            r'\subbottom[' + s.marker + r']{',
            r'\includegraphics[width=0.3\textwidth,scale=0.10]{' + chart_file + r'}',
            r'}',
            r'\hfill',
        ])

    buf.append('\\bottomrule\n\\end{tabular}')

    charts.append(r'\end{figure}')

    template = template.replace('TABLE-MARKER-SUMMARY', '\n'.join( buf ))

    template = template.replace('CHART-ALLELE', '\n'.join( charts ))


    ##
    ## SAMPLE-SUMMARY by SITE
    ##

    buf = []
    buf.append(
        '\\begin{table}[H]\n'
        '\\begin{tabular}{lrrrrrrrrrl}\n'
        '\\toprule\n'
        ' & & \multicolumn{4}{c}{Multiplicity of Infection} & \multicolumn{2}{c}{Polyclonality} & \\tabularnewline\n'
        '\\cmidrule(r){3-6} \\cmidrule(r){7-8}\n'
        'Location & N & Mean & Med & Min & Max & Prop & N & He & LD & p-val\\tabularnewline\n'
        '\\midrule'
    )

    for r in data['location_summary']:
        if r[1] < 20:
            location_name = '\\textcolor{red}{%s}'
        elif r[1] < 30:
            location_name = '\\textcolor{yellow}{%s}'
        else:
            location_name = '%s'
        buf.append( 
            '%s & %d & %1.2f & %d & %d & %d & %1.2f & %d & %1.3f & %s & %s\\tabularnewline\n' %
            ( location_name % r[0], r[1], r[2], r[3], r[4], r[5], r[6]/r[1], r[6], r[7], r[8], r[9]) )
        

    buf.append('\\bottomrule\n\\end{tabular}\n\\end{table}\n')

    template = template.replace('TABLE-SAMPLE-SUMMARY',
            '\n'.join( buf ) )

    ##
    ## SAMPLE-LD by SITE
    ##

    buf = []
    buf.append(
        '\\begin{table}[H]\n'
        '\\begin{tabular}{lrrrrrrrrr}\n'
        '\\toprule\n'
        ' & \multicolumn{3}{c}{Sample set a)} & \multicolumn{3}{c}{Sample set b)} & \multicolumn{3}{c}{Sample set c)} \\tabularnewline\n'
        '\\cmidrule(r){2-4} \\cmidrule(r){5-7} \\cmidrule(r){8-10} \n'
        'Location & N & LD & p-val & N & LD & p-val & N & LD & p-val\\tabularnewline\n'
        '\\midrule'
    )

    for r in data['location_summary']:
        if r[1] < 20:
            location_name = '\\textcolor{red}{%s}'
        elif r[1] < 30:
            location_name = '\\textcolor{yellow}{%s}'
        else:
            location_name = '%s'
        buf.append( 
            '%s & %d & %s & %s & %d & %s & %s & %d & %s & %s\\tabularnewline\n' %
            ( location_name % r[0], r[1], r[8], r[9], r[10], r[11], r[12], r[13], r[14], r[15]) )

    buf.append('\\bottomrule\n\\end{tabular}\n\\end{table}\n')

    template = template.replace('TABLE-SAMPLE-LD',
            '\n'.join( buf ))


    ## FST
    
    fst = data['Fst']
    buf = []
    buf.append(
        '\\begin{table}[H]\n'
        '\\tiny\n'
        '\\begin{tabular}{l%s}\n'
        '\\toprule\n' % ('c' * len(fst.fst_m))
    )

    buf.append( 'Location & ' + ' & '.join( fst.get_labels() ) + ' \\tabularnewline' )
    buf.append( '\\midrule' )

    for i in range(len(fst.fst_m)):
        n = len( fst.sets[i] )
        if n < 20:
            loc = '\\textcolor{red}{%s}'
        elif n < 30:
            loc = '\\textcolor{yellow}{%s}'
        else:
            loc = '%s'
        
        buf.append('%s & ' % (loc % fst.labels[i+1]) + (' & '.join( fst.fst_m[i] )).replace('+-', ' \\(\\pm\\) ') + ' \\tabularnewline' )

    buf.append(
        '\\bottomrule\n\\end{tabular}\n\\end{table}'
    )

    template = template.replace( 'TABLE-FST', '\n'.join( buf ) )


    ## genotype distance 

    counts = np.bincount( data['distance'].D )
    counts = counts / sum(counts)

    vline_file = directory + 'distance-dist.pdf'
    plt.vlines( range( len(counts) ), [0], counts )
    plt.xlim( -0.5, len(counts) - 0.5 )
    plt.xlabel('number of mismatch markers/locuses')
    plt.ylabel('pairwise frequency')
    plt.savefig( vline_file )
    plt.close()

    template = template.replace('CHART-DISTANCE-DISTRIBUTION',
                include_graphics( vline_file ) )

    #njtree_file = nj_distance( 
    #    list( '" ' + Sample.get(idx).code + ' "' for idx in data['genotypes'].index ),
    #    data['distance'][0],
    #    directory )
    njtree_file = nj_tree( data['distance'], directory )
    template = template.replace('PLOT-NJTREE', include_graphics( njtree_file ))

    njtree_file = nj_tree( data['strict_distance'], directory )
    template = template.replace('PLOT-STRICT-NJTREE', include_graphics( njtree_file ))


    pca_file = plot_pca( data['pca'], data['distance'], directory, 'distance-pca.pdf' )
    template = template.replace( 'CHART-DISTANCE-PCA',
                include_graphics( pca_file ) )

    pca_file = plot_pca( data['strict_pca'], data['strict_distance'], directory,
                'strict-distance-pca.pdf' )
    template = template.replace( 'CHART-STRICT-DISTANCE-PCA',
                include_graphics( pca_file ) )

    return template


def include_graphics(filename, scale=0.50):

    lines = [ r'\begin{figure}[H]', r'\centering' ]
    lines.append( r'\includegraphics[scale=' + str(scale) + ']{' + filename + r'}' )
    lines.append( r'\end{figure}' )

    return '\n'.join( lines )


def generate_report_2( batchcode, querytext, marker_ids,
                allele_absolute_threshold, allele_relative_threshold,
                sample_quality_threshold, marker_quality_threshold,
                location_level, spatial_differentiation, temporal_differentiation,
                template_file, fmt = 'PDF' ):

    report = ReportResult()

    # prepare the query
    fullquery = ''
    if batchcode:
        fullquery += ' | '.join( '%s[batch]' % batch for batch in batchcode.split() )
    if querytext:
        fullquery += querytext

    if not fullquery:
        raise RuntimeError( 'Please provide batch code or querytext' )

    sample_ids = parse_querycmd( fullquery )

    tmp_dir = get_temp_path( random_string(8) )
    os.mkdir( tmp_dir )
    tmp_dir += '/'

    result = generate_comprehensive_summary_2( 
                sample_ids = sample_ids, querysets = None, marker_ids = marker_ids,
                location_level = location_level,
                spatial_differentiation = spatial_differentiation,
                temporal_differentiation = temporal_differentiation,
                allele_absolute_threshold = allele_absolute_threshold,
                allele_relative_threshold = allele_relative_threshold,
                sample_quality_threshold = sample_quality_threshold,
                marker_quality_threshold = marker_quality_threshold,
                tmp_dir = tmp_dir )

    # format the TeX file

    tex_filename = tmp_dir + 'report.tex'

    #template = open( template_file ).read()

    template = format_tex_report( template_file, result, tmp_dir )

    with open(tex_filename, 'w') as f:
        f.write( template )

    if fmt == 'PDF':
        # run pdflatex here
        ok = call([   'pdflatex',
                    '-halt-on-error',
                    '-output-directory', tmp_dir,
                    tex_filename
                ])
        if ok != 0:
            raise SysError('pdflatex returned error code: %d, produced with TeX source at %s'
                    % (ok, tex_filename))
        report.fullpath = tmp_dir + 'report.pdf'
        return report

    raise SysError('should not be here!')


def generate_report_3( baseparams, location_level,
                spatial_differentiation, temporal_differentiation,
                detection_differentiation,
                template_file, fmt = 'PDF' ):

    report = ReportResult()

    # prepare the query
    sample_sets = parse_advquerycmd( baseparams.queryset )

    tmp_dir = get_temp_path( random_string(8) )
    os.mkdir( tmp_dir )
    tmp_dir += '/'

    result = generate_comprehensive_summary_3( 
                sample_sets = sample_sets,
                baseparams = baseparams,
                location_level = location_level,
                spatial_differentiation = spatial_differentiation,
                temporal_differentiation = temporal_differentiation,
                detection_differentiation = detection_differentiation,
                tmp_dir = tmp_dir )

    # format the TeX file

    tex_filename = tmp_dir + 'report.tex'

    #template = open( template_file ).read()

    template = format_tex_report( template_file, result, tmp_dir )

    with open(tex_filename, 'w') as f:
        f.write( template )

    if fmt == 'PDF':
        # run pdflatex here
        ok = call([   'pdflatex',
                    '-halt-on-error',
                    '-output-directory', tmp_dir,
                    tex_filename
                ])
        if ok != 0:
            raise SysError('pdflatex returned error code: %d, produced with TeX source at %s'
                    % (ok, tex_filename))
        report.fullpath = tmp_dir + 'report.pdf'
        return report

    raise SysError('should not be here!')


def format_tex_report( template_dir, report, tmp_dir ):

    tex_header = open( template_dir + '/header.tex' ).read()
    tex_footer = open( template_dir + '/footer.tex' ).read()

    buf = []
    buf.append( tex_header )


    # BASIC SUMMARIES

    buf.extend( format_tex_basic_summaries( report['basic'] ) )

    # DATA QUALITY FEATURES

    buf.append( r'\section*{2. Data Quality Features}' )

    buf.extend( format_tex_sample_quality( report['sample_quality'] ) )
    buf.extend( format_tex_marker_quality( report['marker_quality'] ) )

    # POPULATION GENETICS STATISTICS

    buf.extend( [
        r'\section*{3. Population Genetics Statistics}', '',
        r'\paragraph*{Notes on data set}', '',
        r'\begin{enumerate}',
        r'\item Unless stated, only filtered baseline samples (i.e. non-recurrent samples) were included in the analysis.',
        r'\item A minimal threshold of 30 samples is generally advised for population genetic studies.  Caution is therefore advised in the interpretation of results derived from sample sets with lower sample size. In this report, results derived from sample sets with less than 30 samples are highlighted as a reminder that caution is advised in interpretation.',
        r'\item For each sample, at each marker, the predominant allele (maximum height peak), and any additional alleles with peak height >= ?' + r'\% the height of the predominant allele were scored. The implementation of a peak intensity threshold facilitates comparability between samples and populations by reducing potential bias in polyclonality estimates arising from differences in sample DNA (see [3]).',
        r'\item In several analyses (details in the notes below), only the predominant allele at each marker in each sample was used to ensure an unbiased estimate of the minor allele frequency (see [3])',
        r'\end{enumerate}', ''
    ] )

    buf.extend( format_tex_marker_summary( report['marker_summary']['markers'], tmp_dir ) )

    buf.append( r'\subsection*{Figure 3.2a - Polyclonality by Markers}' )
    buf.extend(format_tex_marker_polyclonality( report['marker_summary']['markers'], tmp_dir ))

    buf.append( r'\subsection*{Figure 3.2b - Polyclonality Rank by He}' )
    buf.extend( format_tex_rank_polyclonality( report['marker_summary']['clonality_by_he'],
                tmp_dir, 'he') )

    buf.append(  r'\subsection*{Figure 3.2c - Polyclonality Rank by Polyclonals}' )
    buf.extend( format_tex_rank_polyclonality( report['marker_summary']['clonality_by_prop'],
                tmp_dir, 'prop') )
    
    # BASIC POPULATION GENETICS STATS AND FST
    
    buf.append( r'\subsection*{Table 3.2 - Genetic Differentiation Summary}' )
    buf.extend( format_tex_differentiation( report['diff_summary'] ))

    buf.append( r'\subsection*{Table 3.3 - LD by Differentiation}' )
    buf.extend( format_tex_ld( report['diff_summary'] ))

    buf.append( r'\subsection*{Table 3.4 - FST by Differentiation}' )
    buf.extend( format_tex_fst( report['Fst']))

    buf.append( r'\subsection*{Table 3.5 - FST (max) by Differentiation (recoded alleles)}' )
    buf.extend( format_tex_fst( report['Fst_max']))

    buf.append( r'\subsection*{Table 3.6 - FST (std) by Differentiation (FST / FST (max))}' )
    buf.extend( format_tex_fst( report['Fst_std']))

    buf.append( r'\paragraph*{Notes on Tables 3.1 - 3.4}' )
    buf.extend( notes_genetic_diff )

    
    # NEIGHBOR JOINING
    
    buf.append( r'\subsection*{Figure 3.3a - Unrooted Neighbor-Joining tree - all samples}' )
    buf.extend( format_tex_nj( report['base_distance'], tmp_dir))

    buf.append( r'\subsection*{Figure 3.3b - Unrooted Neighbor-Joining tree - strict samples}')
    buf.extend( format_tex_nj( report['strict_distance'], tmp_dir))

    buf.append( r'\paragraph*{Notes on Figures 3.3a and 3.3b}' )
    buf.extend( notes_nj )    
    
    # PCA

    buf.append( r'\subsection*{Figure 3.4a - Principal Component Analysis - all samples}' )   
    buf.extend( format_tex_pca( report['base_pca'], report['base_distance'],
                    tmp_dir, 'base-pca.pdf' ))

    buf.append( r'\subsection*{Figure 3.4b - Principal Component Analysis - strict samples}' )
    buf.extend( format_tex_pca( report['strict_pca'], report['strict_distance'],
                    tmp_dir, 'strict-pca.pdf' ))

    buf.append( r'\paragraph*{Notes on Figure 3.4}' )
    buf.extend( notes_pca )


    buf.append( tex_footer )

    return '\n'.join( buf )


def format_tex_basic_summaries( report ):

    buf = []

    buf.extend( [
        r'\section*{1. Sample and Marker Features}', '',
        r'\subsection*{Table 1.1 - Study site(s) and sample numbers - baseline population}',''
        ])

    buf.append(
            '\\begin{tabular}{lr}\n\\toprule\nLocation & N\\tabularnewline\n\\midrule'
        )
    for (location, n) in report['locations'].iteritems():
        buf.append( "%s & %d \\tabularnewline" % (location, n) )
    buf.append('\\bottomrule\n\\end{tabular}')

    buf.extend( [
        r'\subsection*{Table 1.2 - Sample collection dates (in year)}',''
        ])

    buf.append(
        '\\begin{tabular}{llr}\n\\toprule\nYear & Location & N\\tabularnewline\n\\midrule'
    )
    Y = report['years']
    current_year = 0
    for (index, n) in Y.items():
        year, location = index
        if year == current_year:
            buf.append( " & %s & %d \\tabularnewline" % (location, n) )
        else:
            current_year = year
            buf.append( "%d & %s & %d \\tabularnewline" % ( year, location, n ) )
    buf.append('\\bottomrule\n\\end{tabular}')

    return buf


def format_tex_sample_quality( report ):

    buf = [ r'\subsection*{Table 2.1 - Sample Failure Rate}', '' ]

    buf.append(
        '\\begin{tabular}{lrrrrrrr}\n'
        '\\toprule\n'
        ' & & \\multicolumn{4}{c}{Failed Genotyping} & \\multicolumn{2}{c}{Failed Samples} \\tabularnewline\n'
        '\\cmidrule(r){3-6} \\cmidrule(r){7-8}\n'
        'Location & N & Mean & Median & Min & Max & N & (\\%) \\tabularnewline\n'
        '\\midrule\n'
    )

    total = 0
    failed = 0
    for (location, failed_genotypes, failed_samples) in report:
        buf.append(
            '%s & %d & %3.2f & %d & %d & %d & %d & %d \\%% \\tabularnewline' %
            (location, len(failed_genotypes),
                np.mean(failed_genotypes), np.median(failed_genotypes),
                min(failed_genotypes), max(failed_genotypes),
                failed_samples, round(100.0 * failed_samples/len(failed_genotypes)) )
        )
        total += len(failed_genotypes)
        failed += failed_samples
    buf.append('\\bottomrule\n\\end{tabular}')

    buf.append('')
    buf.append('Total filtered samples: %d of %d\\tabularnewline' % (total-failed, total))

    return buf


def format_tex_marker_quality( report ):

    buf = [ r'\subsection*{Table 2.2 - Filtered Marker Quality}', '' ]

    buf.append(
        '\\begin{tabular}{lrrc}\n\\toprule\n & \multicolumn{2}{c}{Failed Genotyping} & \\tabularnewline\n\\cmidrule(r){2-3}\nMarker & No. & (\\%) & Included in haplotyping\\tabularnewline\n\\midrule'
    )
    for (code, marker_id, no, prop, state) in report:
        buf.append('%s & %d & %d \\%% & %s\\tabularnewline' % (
            code, no, prop, 'Yes' if state else 'No' ))
    buf.append('\\bottomrule\n\\end{tabular}')

    buf.append(
        '\n'
        '\\paragraph*{Notes}\n'
        '\n'
        '\\begin{enumerate}\n'
        '\\item Genotyping fail = absence of an allele call at a given marker. Percentages are calculated using the total number of samples in the study as the denominator.\n'
        '\\item Arbitrary cut-off of <10\% genotyping failure rate for inclusion.\n'
        '\\end{enumerate}\n'
        '\n'
    )

    return buf


def format_tex_marker_summary( report, directory ):

    buf = [ '',
        r'\subsection*{Table 3.1 - Summary Statistics by Markers}', ''
        ]

    buf.append(
        '\\begin{tabular}{lrrrrrrr}\n'
        '\\toprule\n'
        '& & \multicolumn{4}{c}{Alleles per sample} & \\tabularnewline\n'
        '\\cmidrule(r){3-6}\n'
        'Marker & Unique Allele & Mean & Median & Min & Max & Expected He & Polyclonals\\tabularnewline\n'
        '\\midrule'
    )

    charts = [ 
        r'\subsection*{Figure 3.1 - Allele Frequency}', '',
        r'\begin{figure}[H]', r'\centering' ]

    colors = cm.Accent( [ x/1000 for x in range(0,1001,125) ] )

    codes = []
    for (code, m, unique, stats, he, polyclonals, allele_dist, sample_dist) in report:
        buf.append('%s & %d & %1.2f & %d & %d & %d & %3.2f & %d \\tabularnewline' %
            ( code, unique, stats[0], stats[1], stats[2], stats[3], he, polyclonals ))

        # generate chart as well

        chart_file = directory + 'marker-%d-pie.pdf' % m

        plt.pie( list(reversed(sorted(allele_dist))), startangle=90, colors = colors )
        plt.axis('equal')
        plt.savefig(chart_file)
        plt.close()

        charts.extend( [ 
            r'\subbottom[' + code + r']{',
            r'\includegraphics[width=0.3\textwidth,scale=0.10]{' + chart_file + r'}',
            r'}',
            r'\hfill',
        ])

    buf.append('\\bottomrule\n\\end{tabular}')

    charts.append(r'\end{figure}')

    return buf + charts


def format_tex_marker_polyclonality( report, directory ):

    codes = []
    polyclonality = []
    for (code, m, unique, stats, he, polyclonals, allele_dist, sample_dist) in report:
        codes.append( code )
        polyclonality.append( polyclonals )

    plot_file = directory + 'marker-polyclonality-plot.pdf'

    width = 0.35
    ind = np.arange( len(codes) )
    plt.bar( ind, polyclonality, width = width )
    plt.ylabel('% polyclonality')
    plt.xlabel('Markers')
    plt.xticks(ind + width/2, codes )
    plt.savefig( plot_file )
    plt.close()

    return [ '', include_graphics( plot_file ) ]


def format_tex_rank_polyclonality( report, directory, tag ):

    polyclonality = []
    codes = []
    for polyclonals, code in report:
        polyclonality.append( polyclonals )
        codes.append( code )

    N = polyclonality[-1]
    if N == 0:
        polyclonality = [ 0 for x in polyclonality ]
    else:
        polyclonality = [ x/N for x in polyclonality ]

    plot_file = directory + 'rank-polyclonality-'+tag+'-plot.pdf'

    width = 0.35
    ind = np.arange( len(codes) )
    plt.bar( ind, polyclonality, width = width )
    plt.ylabel('% polyclonality')
    plt.xlabel('Markers')
    plt.xticks(ind + width/2, ind + 1 )
    plt.savefig( plot_file )
    plt.close()

    return [ '', include_graphics( plot_file ) ]


def format_tex_differentiation( report ):
    
    buf = [ '' ]
    
    buf.append(
        '\\begin{table}[H]\n'
        '\\begin{tabular}{lrrrrrrrr}\n'
        '\\toprule\n'
        ' & & \multicolumn{4}{c}{Multiplicity of Infection} & \multicolumn{2}{c}{Polyclonality} & \\tabularnewline\n'
        '\\cmidrule(r){3-6} \\cmidrule(r){7-8}\n'
        'Location & N & Mean & Med & Min & Max & Prop & N & Expected He \\tabularnewline\n'
        '\\midrule'
    )

    for r in report:
        if r[1] < 20:
            label = '\\textcolor{red}{%s}'
        elif r[1] < 30:
            label = '\\textcolor{yellow}{%s}'
        else:
            label = '%s'
        m = r[2]
        buf.append( 
            '%s & %d & %1.2f & %d & %d & %d & %1.2f & %d & %1.3f \\tabularnewline\n' %
            ( label % r[0], r[1], m[0], m[1], m[2], m[3], m[5], m[6], r[3]) )
        

    buf.append('\\bottomrule\n\\end{tabular}\n\\end{table}\n')

    return buf


def format_tex_ld( report ):

    buf = [ '' ]
    buf.append(
        '\\begin{table}[H]\n'
        '\\begin{tabular}{lrrrrrrrrr}\n'
        '\\toprule\n'
        ' & \multicolumn{3}{c}{Sample set a)} & \multicolumn{3}{c}{Sample set b)} & \multicolumn{3}{c}{Sample set c)} \\tabularnewline\n'
        '\\cmidrule(r){2-4} \\cmidrule(r){5-7} \\cmidrule(r){8-10} \n'
        'Location & N & LD & p-val & N & LD & p-val & N & LD & p-val\\tabularnewline\n'
        '\\midrule'
    )

    for r in report:
        if r[1] < 20:
            location_name = '\\textcolor{red}{%s}'
        elif r[1] < 30:
            location_name = '\\textcolor{yellow}{%s}'
        else:
            location_name = '%s'
        n, s, u = r[4], r[5], r[6]
        buf.append( 
            '%s & %d & %s & %s & %d & %s & %s & %d & %s & %s\\tabularnewline\n' %
            (   location_name % r[0],
                len(n), n.get_LD(), n.get_pvalue(),
                len(s), s.get_LD(), s.get_pvalue(),
                len(u), u.get_LD(), u.get_pvalue()
            ) )

    buf.append('\\bottomrule\n\\end{tabular}\n\\end{table}\n')

    return buf

    
def format_tex_fst( fst ):
    
    buf = [ '' ]
    buf.append(
        '\\begin{table}[H]\n'
        '\\tiny\n'
        '\\begin{tabular}{l%s}\n'
        '\\toprule\n' % ('c' * len(fst.fst_m))
    )

    buf.append( 'Location & ' + ' & '.join( '\\shortstack[c]{%s}' % x.replace('|', '\\\\') for x in fst.get_labels() ) + ' \\tabularnewline' )
    buf.append( '\\midrule' )

    for i in range(len(fst.fst_m)):
        n = len( fst.sets[i] )
        if n < 20:
            loc = '\\textcolor{red}{%s}'
        elif n < 30:
            loc = '\\textcolor{yellow}{%s}'
        else:
            loc = '%s'
        
        buf.append('%s & ' % (loc % fst.labels[i+1]) + (' & '.join( '\\shortstack[c]{%s}' % x for x in fst.fst_m[i] )).replace('+-', ' \\(\\pm\\) ') + ' \\tabularnewline' )

    buf.append(
        '\\bottomrule\n\\end{tabular}\n\\end{table}'
    )

    return buf


def format_tex_nj( pwdist, directory ):

    njtree_file = nj_tree( pwdist, directory )
    return [ include_graphics( njtree_file ) ]


def format_tex_pca( pca, pwdist, directory, filename ):

    pca_file = plot_pca( pca, pwdist, directory, filename )
    return [ include_graphics( pca_file )]



## NOTES are here (to clean the codebase)

notes_genetic_diff = [
        '',
        r'\begin{enumerate}',
        r'\item Number of alleles = the number of different alleles observed in the sample population.',
        r'\item Median MOI and range. MOI = multiplicity of infection. The MOI in each sample is defined by the maximum number of alleles observed at any n markers tested. The MOI provides a lower bound estimate of the number of genetically distinct parasite clones within a sample.',
        r'\item Proportion of polyclonal samples = number of samples with more than one allele at any of the n markers tested divided by total number of samples.',
        r'\item Expected heterozygosity (HE) provides a measure of population diversity at a given marker (Table 3.1) or averaged across a range of markers for a given sample set (Table 3.2).  The expected heterozygosity for each marker is calculated using the equation given below, where \(p_i\) is the frequency of the \(i\)th of \(k\) alleles. Values range from 0 (no diversity) to nearly 1 (large number of equally frequent alleles). Only the predominant allele at each marker in each sample was used.', '',

        r'\[',
        r'He =  \frac{n}{n-1} (1 - \sum_{i=1}^{k} p_i^2)',
        r'\]',
        '',
        r'\item Table 3.3 details. Multi-locus linkage disequilibrium (LD) was assessed by the standardised index of association (ISA) using the web-based LIAN 3.5 software [4]. Testing the null hypothesis of linkage equilibrium, the significance of the ISA estimates was assessed using 10,000 random permutations of the data. Markers with a high rate of genotyping failures were excluded from the analysis (see Table 2.2). Only samples with no missing data at any of the markers investigated were included in the analysis. Only the predominant allele at each marker in each sample was used. Three sample sets were analyzed:', '',

        r'\begin{enumerate}',
        r'\item All samples (assuming that the predominant alleles at different loci should all belong to the same clone even in polyclonal infections)',
        r'\item Only samples with a maximum of 1 marker with multiple alleles',
        r'\item Unique haplotypes only: each unique multi-locus haplotype observed in sample set a. is presented just once. This analysis enables identification of potential clonal expansions, whereby the ISA is expected to drop substantially in the unique haplotype set relative to the full sample set.',
        r'\end{enumerate}', '',

        r'\item Table 3.4 details. Pair-wise FST values are presented in the lower triangle. Pair-wise FST values were measured using the Arlequin software (version 3.5) [5]. The upper triangle contains the \(p\)-value of the pair-wise FST and its standard deviation.', '',

        r'\item Table 3.5 details. Pair-wise FST values similar to Table 3.4, but with all alleles recoded so that each allele was only spesific only for its respective population.', '',

        r'\end{enumerate}', '' ]


notes_nj = [
    '',
    r'A neighbour-joining tree [7] was generated from the genetic distance matrix using the Analyses of Phylogenetics and Evolution (APE) package in the R software [8]. Markers with a high rate of genotyping failures were excluded from the analysis (see Table 2.2). Only samples with no missing data at any of the markers investigated were included in the analysis. Only the predominant allele at each marker in each sample was used. Two sample sets were analyzed:',
    r'\begin{enumerate}',
    r'\item All samples (assuming that the predominant alleles at different loci should all belong to the same clone even in polyclonal infections)',
    r'\item Only samples with a minimum of 1 marker with multiple alleles',
    r'\end{enumerate}'

]

notes_pca = [
        '',
        r'The PCA (Principal Component Analysis) is a method that can cluster data which have similar features. This plot was generated using the same genetic distance matrix as the one for Neighbor-joining tree. The function \textit{pca} from MDP module of Python programming language was employed to obtain the pca matrix, with matplotlib library as the plotting library.',
        ''
]


