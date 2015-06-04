
import sys, os
import argparse



def init_argparser():

    parser = argparse.ArgumentParser( "" )

    parser.add_argument('--batch', required=True,
                help = 'batch code' )
    parser.add_argument('--user', '-u',
                help = 'user name' )
    parser.add_argument('--output', required=True,
                help = 'file output' )

    return parser


def main(args):

    pass

