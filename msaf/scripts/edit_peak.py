

import sys, os, io
import argparse
import transaction
from msaf.models import Allele, AlleleSet, Sample, Batch, Marker, EK, dbsession

def init_argparser():

    parser = argparse.ArgumentParser( '' )


    return parser


def main(args):

    with transaction.manager:
        edit_peak( args )

    print('Done!')


def edit_peak( args ):

    pass
