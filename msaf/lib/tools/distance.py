
import numpy as np
import matplotlib.pyplot as plt
import mdp
from subprocess import call

from msaf.models import Sample
from rhombus.lib.utils import random_string

from msaf.lib.analytics import get_genotypes


def jitters( data ):
    """ returning jittered data with normal distribution noise """
    # need to calculate s based on the smallest and longest distance of the points
    d_min = d_max = np.abs(data[0] - data[1])
    for i in range(len(data)):
        for j in range(len(data)):
            d = np.abs( data[i] - data[j] )
            if d > 0:
                if d > d_max:
                    d_max = d
                elif d < d_min:
                    d_min = d

    s = d_min / d_max * len(data) / 2
    print("Jitters:", s)
    return s * np.random.randn( len(data) )

def pw_distance_2( genotypes ):

    n = len(genotypes)
    m = np.zeros( (n, n) )
    g = genotypes.values
    v = []
    l = len(g[0])

    for i in range(0, n):
        for j in range( i, n):
            d = sum( 1 if x != y else 0 for (x,y) in zip( g[i], g[j] ) )
            m[i,j] = m[j,i] = d/l
            v.append( d )

    return (m, v)


def pca_distance( m ):
    # perform PCA, add random noise based on how much the data spread

    comps = mdp.pca( m, output_dim = 2 )
    a = comps[1,0]
    comps[:,0] += jitters( comps[:,0] )
    b = comps[1,0]
    assert a != b
    comps[:,1] += jitters( comps[:,1] )

    return comps


def nj_distance( names, m, tempdir ):
    """ run R's ape to create NJ and display tree """

    # prepare a file for the matrix

    file_id = random_string(3)
    matrix_file = tempdir + 'matrix-distance-%s.txt' % file_id
    script_file = tempdir + 'njtree-%s.r' % file_id
    njtree_file = tempdir + 'njtree-%s.pdf' % file_id

    with open(matrix_file, 'w') as out:
        out.write( '\t'.join( names ) )
        out.write( '\n')
        for name, vals in zip( names, m ):
            out.write( '%s\t%s\n' % (name, '\t'.join( ['%2.3f' % x for x in vals] ) ))

    with open(script_file, 'w') as scriptout:
        scriptout.write("""
library(ape)
M <- as.matrix( read.table("%s", sep='\t', header=T) )
tree <- nj( M )
pdf("%s")
plot(tree, "fan", font=1, cex=0.5)
""" % (matrix_file, njtree_file) )

    ok = call( ['Rscript', script_file] )

    if ok != 0:
        raise RuntimeError("Rscript run unsucessfully")

    return njtree_file


class DistanceMatrix(object):

    def __init__(self):
        self.genotype_sets = []
        self.G = None
        self.M = None
        self.L = None
        self.C = None
        self.D = None
        self.S = []

    def add_genotype_set(self, genotype_set):
        self.genotype_sets.append( genotype_set )

    def modify_labels(self, modifier):
        try:
            self.L = [ modifier[str(x)] for x in self.L ]
        except KeyError as e:
            raise RuntimeError( 'Label modifier does not contain entry for %s' % str(x) )
        


def pw_distance( genotype_sets ):
    """ return a distance matrix """

    DM = DistanceMatrix()

    for (gs, genotypes) in get_genotypes(genotype_sets):
        if len(gs) == 0:
            continue
        DM.add_genotype_set( gs )
        if DM.G is None:
            DM.G = genotypes
            DM.C = [ gs.get_colour() ] * len(DM.G)
            DM.S = [ ( gs, 0, len(DM.G)) ]
            continue
        DM.S.append( ( gs, len(DM.G), len(genotypes)) )
        DM.G = DM.G.append( genotypes ) # Pandas Dataframe, not Python list
        DM.C += [ gs.get_colour() ] * len( genotypes )
    
    DM.M, DM.D = pw_distance_2( DM.G )
    DM.L = [ Sample.get(x).code for x in DM.G.index ]
    return DM

def nj_tree( aDistanceMatrix, tempdir = None, fmt='pdf' ):

    file_id = random_string(3)

    matrix_file = tempdir + 'matrix-distance-%s.txt' % file_id
    colors_file = tempdir + 'colors-distance-%s.txt' % file_id
    script_file = tempdir + 'njtree-%s.r' % file_id
    njtree_file = tempdir + 'njtree-%s.%s' % (file_id, fmt)
    
    with open(matrix_file, 'w') as out_m, open(colors_file, 'w') as out_c:

        out_m.write( '\t'.join( aDistanceMatrix.L ) )
        out_m.write( '\n')
        for name, vals in zip( aDistanceMatrix.L, aDistanceMatrix.M ):
            out_m.write( '%s\t%s\n' % (name, '\t'.join( ['%2.3f' % x for x in vals] ) ))

        out_c.write('\n'.join( aDistanceMatrix.C ) )

    with open(script_file, 'w') as scriptout:
        if fmt == 'pdf':
            cmd = 'pdf("%s", width = 11.2, height=7)' % njtree_file
        elif fmt == 'png':
            cmd = 'png("%s", width = 1024, height = 640)' % njtree_file
        scriptout.write("""
library(ape)
M <- as.matrix( read.table("%s", sep='\t', header=T) )
C <- as.vector( read.table("%s", sep='\t', header=F)[,1] )
tree <- nj( M )
%s
plot(tree, "fan", tip.color = C, font=1, cex=0.7, label.offset = 0.009)
legend('topright', inset=c(0,0), c(%s), col = c(%s), lty=1, cex=0.85, xpd=T)
""" % (matrix_file, colors_file, cmd,
        ",".join( '"%s"' % e.get_label() for e in aDistanceMatrix.genotype_sets),
        ",".join( '"%s"' % e.get_colour() for e in aDistanceMatrix.genotype_sets) )
    )

    ok = call( ['Rscript', script_file] )

    if ok != 0:
        raise RuntimeError("Rscript run unsucessfully")

    return njtree_file

#legend('topright', inset=c(-0.2,0), c(%s), col = c(%s), lty=1, cex=0.6, xpd=T)


def pca_distance( aDistanceMatrix, dim = 2 ):

    comps = mdp.pca( aDistanceMatrix.M, output_dim = 2 )
    a = comps[1,0]
    comps[:,0] += jitters( comps[:,0] )
    b = comps[1,0]
    #assert a != b
    comps[:,1] += jitters( comps[:,1] )


    return comps


def pca_distance2( aDistanceMatrix, dim = 2):

    pcan = mdp.nodes.PCANode( output_dim = dim )
    pcar = pcan.execute( aDistanceMatrix.M )

    for i in range(dim):
        pcar[:,i] += jitters( pcar[:,i] )


    return (pcar, pcan.d)


def plot_pca2( pca_result, distance_matrix, pc1, pc2, directory=None, filename=None ):
    """ return the full path of pca plot """

    if not directory:
        raise RuntimeError

    if not filename:
        raise RuntimeError

    pca_file = directory + filename

    fig = plt.figure()
    ax = fig.add_subplot(111)

    pca_matrix = pca_result[0]
    pca_var = pca_result[1]

    for gs, s, e in distance_matrix.S:
        ax.scatter( pca_matrix[s:s+e, pc1],
                    pca_matrix[s:s+e, pc2],
                    c = gs.get_colour(),
                    edgecolor = gs.get_colour(),
                    label = gs.get_label(),
                    alpha = 0.75,
                    marker='+',
                    s = 30
        )
    ax.set_xlabel('PC%d (%.3f%%)' % (pc1 + 1, pca_var[pc1]))
    ax.set_ylabel('PC%d (%.3f%%)' % (pc2 + 1, pca_var[pc2]))
    leg = ax.legend(loc='upper left', scatterpoints=1, fontsize='x-small', fancybox=True,
            bbox_to_anchor=(1,1))
    #leg.get_frame().set_alpha(0.5)
    fig.savefig( pca_file, bbox_extra_artists=(leg,), bbox_inches='tight' )
    plt.close()
    return pca_file



def plot_pca( pca_matrix, distance_matrix, directory=None, filename=None ):
    """ return the full path of pca-plot """

    if not directory:
        raise RuntimeError

    if not filename:
        raise RuntimeError

    pca_file = directory + filename

    fig = plt.figure()
    ax = fig.add_subplot(111)

    for gs, s, e in distance_matrix.S:
        ax.scatter( pca_matrix[s:s+e,0],
                    pca_matrix[s:s+e,1],
                    c = gs.get_colour(),
                    edgecolor = gs.get_colour(),
                    label = gs.get_label(),
                    alpha = 0.75,
                    marker='+',
                    s = 30
        )
    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')
    leg = ax.legend(loc='upper left', scatterpoints=1, fontsize='x-small', fancybox=True,
            bbox_to_anchor=(1,1))
    #leg.get_frame().set_alpha(0.5)
    fig.savefig( pca_file, bbox_extra_artists=(leg,), bbox_inches='tight' )
    plt.close()
    return pca_file

