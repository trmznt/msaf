
from msaf.configs import get_libexec_path
from msaf.lib.tools.export import export_flat
from msaf.lib.querycmd import parse_querycmd
from msaf.lib.tools.genotype import dominant_genotypes
from subprocess import Popen, PIPE


class LianResult(object):

    def __init__( self, output, error, n ):
        self.output = output.decode('ASCII')
        self.error = error
        self.ld = ''
        self.pval = ''
        self.n = n
        self.parse()

    def __len__(self):
        return self.n

    def get_LD(self):
        return self.ld

    def get_pvalue(self):
        return self.pval

    def get_output(self):
        return self.output

    def parse(self):
        for line in self.output.split('\n'):
            if line.startswith('St. IA'):
                self.ld = line[6:].strip()
            elif line.startswith('P'):
                self.pval = line[2:].strip()


def run_lian( genotypes ):

    if len(genotypes) <= 2:
        r = LianResult( output = b'', error = b'', n = len(genotypes) )
        r.ld = '-'
        r.pval = '-'
        return r
    
    p = Popen([get_libexec_path("lian")],
          stdin=PIPE, stdout=PIPE, stderr=PIPE,
          close_fds=True)
    p.stdin.write( export_flat( genotypes ).read() )
    p.stdin.close()

    result = LianResult( output = p.stdout.read(), error = p.stderr.read(), n = len(genotypes) )

    return result


def lian( querytext, threshold, markers ):

    sample_ids = parse_querycmd( querytext )
    genotypes = dominant_genotypes( sample_ids, threshold, markers )

    return run_lian( genotypes )

    
        

