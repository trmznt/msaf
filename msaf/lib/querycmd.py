
from pyparsing import *
from sqlalchemy import *
from rhombus.models.core import get_userid
from msaf.models import ( Sample, EK, dbsession, QuerySet, queried_samples, Location, Batch,
                            AlleleSet, Allele, Marker )

from plasmoms.models import PlasmoSample

Sample = PlasmoSample

import re


# Word(initial_character_set, body_character_set)

arg = Word(alphanums + '<>=*', alphanums + ' |&<>/*-_.,')
argname = Word(alphanums, alphanums + ':')
start_bracket = Literal('[')
end_bracket = Literal(']')
arg_expr = OneOrMore( arg + Suppress(start_bracket) + argname + Suppress(end_bracket) )
set_expr = Suppress(Literal('#')) + Word(nums)
snapshot_expr = Suppress(Literal('@')) + Word(alphanums)
operand = arg_expr | set_expr

negop = Literal('!')   # NOT
setop = oneOf('& | :') # AND, OR, XOR

# a hack to return virtually false filter
NORESULT = dbsession.query(Sample.id).filter(Sample.id == 0)


def grouper(n, iterable):
    args = [ iter(iterable)] * n
    return zip(*args)

class QueryExpr(object):

    def eval(self):
        raise NotImplemented

# class & expr helpers

def add_latest_alleleset( classes, expr ):
    if AlleleSet not in classes:
        classes.append( AlleleSet )
        #expr.append( AlleleSet.latest == True )

def add_allele( classes ):
    if Allele not in classes:
        classes.append( Allele )

def add_location( classes ):
    if Location not in classes:
        classes.append( Location )

class EvalArgExpr(QueryExpr):
    """ This is the main argument parser which provides the necessary mapping
        to SQLAlchemy query object
    """

    def __init__(self, tokens):
        print("EvalArgExpr tokens:", tokens)
        self.args = grouper(2, tokens)

    def eval(self):
        """ this class handle the heavy-lifting of dealing with the arguments,
            if you need to add certain field please do so here
        """

        classes = []
        expr = []

        for arg, field in self.args:

            field = field.lower()
            arg = arg.strip()
            try:
                if field == 'country':
                    add_location( classes )
                    expr.append( Location.country_id == EK._id( arg ) )
                elif field == 'adminl1':
                    add_location( classes )
                    expr.append( self.eval_arg( arg, Location.level1_id ))
                elif field == 'adminl2':
                    add_location( classes )
                    expr.append( self.eval_arg( arg, Location.level2_id ))
                elif field == 'adminl3':
                    add_location( classes )
                    expr.append( self.eval_arg( arg, Location.level3_id ))
                elif field == 'adminl4':
                    add_location( classes )
                    expr.append( self.eval_arg( arg, Location.level4_id ))
                elif field == 'location':
                    pass
                elif field == 'batch':
                    classes.append( Batch )
                    expr.append( Batch.code.ilike(arg) )
                elif field == 'allele':
                    add_latest_alleleset( classes, expr )
                    add_allele( classes )
                    if '-' in arg:
                        v1, v2 = arg.split('-',1)
                        expr.append( and_( Allele.value >= float(v1),
                                            Allele.value <= float(v2) ) )
                    elif arg.startswith('>='):
                        expr.append( Allele.value >= float(arg[2:]) )
                    elif arg.startswith('<='):
                        expr.append( Allele.value <= float(arg[2:]) )
                    elif arg.startswith('>'):
                        expr.append( Allele.value > float(arg[1:]) )
                    elif arg.startswith('<'):
                        expr.append( Allele.value < float(arg[1:]) )
                    else:
                        expr.append( Allele.value == float(arg) )
                elif field == 'marker':
                    add_latest_alleleset( classes, expr )
                    add_allele( classes )
                    marker = Marker.search( arg )
                    expr.append( Allele.marker_id == marker.id )
                else:
                    raise RuntimeError('unknown field: %s' % field)
            except KeyError:
                return dbsession.query(Sample.id).filter( NORESULT )

        # AD-HOC getting only popgen (non-recurrent) samples

        expr.append( Sample.recurrent == False )

        q = dbsession.query(Sample.id)
        for c in classes:
            q = q.join( c )
        return q.filter( and_( *expr ) )

    def eval_arg(self, arg, identifier):
        if arg[0] == '!':
            return identifier != EK._id( arg[1:] )
        else:
            return identifier == EK._id( arg )


class EvalSetExpr(QueryExpr):

    def __init__(self, tokens):
        self.queryset_id = tokens[0]

    def eval(self):
        queryset = QuerySet.get(self.queryset_id)
        if not queryset or queryset.lastuser_id != get_userid():
            return NORESULT
        return dbsession.query(Sample.id).filter( Sample.id.in_( select([queried_samples.c.sample_id]).where( queried_samples.c.queryset_id == int(self.queryset_id)) ) )


class EvalNegOp(QueryExpr):

    def __init__(self, tokens):
        print("EvalNegOp tokens:", tokens)
        self.value = tokens[0][1]

    def eval(self):
        return dbsession.query(Sample.id).filter( not_( Sample.id.in_( self.value.eval().subquery() ) ) )


class EvalSetOp(QueryExpr):

    def __init__(self, tokens):
        print("EvalSetOp tokens:", tokens)
        self.value = tokens[0]

    def eval(self):

        tokens = self.value[1:]
        eval_1 = self.value[0].eval()

        while tokens:
            op = tokens[0]
            eval_2 = tokens[1].eval()
            tokens = tokens[2:]

            if op == '|':
                eval_1 = union( eval_1, eval_2 )
            elif op == '&':
                eval_1 = intersect( eval_1, eval_2 )
            elif op == ':': # exclusive OR
                eval_1 = except_(
                    dbsession.query(Sample.id).filter( Sample.id.in_( union( eval_1, eval_2) )),
                    dbsession.query(Sample.id).filter( Sample.id.in_( intersect( eval_1, eval_2 )))
                )
            #eval_1 = eval_1.eval()

        return dbsession.query(Sample.id).filter( Sample.id.in_( eval_1 ) )


arg_expr.setParseAction( EvalArgExpr )
set_expr.setParseAction( EvalSetExpr )

cmd_expr = operatorPrecedence( operand,
    [   (negop, 1, opAssoc.RIGHT, EvalNegOp),
        (setop, 2, opAssoc.LEFT, EvalSetOp)
    ])


def parse_querycmd( line, default_field = 'sample' ):
    """ return an sqlalchemy query statement in form of dbsession.query(Sample.id)
        default_field : field used when no field identifier is used
    """

    line = line.strip()

    if line == '*':
        # use all available samples
        return dbsession.query(Sample.id)

    if '[' not in line and not line.startswith('#'):
        # no field and not a query number:
        line += '[' + default_field + ']'

    expr = cmd_expr.parseString( line )

    #return expr
    return expr[0].eval()

    if len(expr) == 1:
        q = dbsession.query( Sample.id ).join( Location ).filter( expr[0].eval() )
    else:
        filters = []
        for e in expr:
            filters.append( e.eval() )
        q = dbsession.query( Sample.id ).join( Location ).filter( and_( *filters ) )

    return q


from sqlalchemy.sql.expression import Executable, ClauseElement
from sqlalchemy.ext.compiler import compiles

class InsertFromSelect(Executable, ClauseElement):
    def __init__(self, table, select):
        self.table = table
        self.select = select

@compiles(InsertFromSelect)
def visit_insert_from_select(element, compiler, **kw):
    return "INSERT INTO %s %s" % (
        compiler.process(element.table, asfrom=True),
        compiler.process(element.select)
    )


def insert_queryset( query, queryset_id ):
    expr = InsertFromSelect(queried_samples,
        #dbsession.query( [literal(str(queryset_id))], Sample.id).filter( Sample.id.in_(query)))
        select([literal(str(queryset_id)).label('queryset_id'), Sample.id]).where( Sample.id.in_(query) ))
    return expr


def get_queries(userid=None):
    """ get previous queries from the current users """
    if userid == None:
        userid = get_userid()
    return QuerySet.query().filter( QuerySet.lastuser_id == userid).order_by(
            QuerySet.id.desc() )

def get_sample_ids(query, userid=None):

    if userid == None:
        userid = get_userid()
    query = query.strip()
    if query.startswith('#'):
        queryset_id = int(query[1:])
        qs = QuerySet.get( queryset_id )
        if qs.lastuser_id != userid:
            # access violation
            pass
        return dbsession.query(Sample.id)

docs = '''
<p>The query text syntax is modelled after
<a href="http://www.ncbi.nlm.nih.gov/books/NBK3837/#EntrezHelp.Entrez_Searching_Options">
NCBI Entrez query syntax</a>, using the square brackets as field selector. Below are some
examples of query text syntax.</p>
<pre>
kudat[town]
</pre>
<pre>
kudat[town] | likas[town]
</pre>

<p>Each of query text syntax consists of one or more text and the associated field descriptor
such as <code>kudat[town]</code> where <code>kudat</code> is the search text and 
<code>[town]</code> is the field selector. Two or more associated field descriptor can be
combined using boolean operators (or set operators) to compose more complex query text,
such as <code>kudat[town] | likas[town]</code> where <code>|</code> is the OR boolean operator.

<h3>Boolean operators</h3>

<p>Boolean operators are used to combine two or more query search.</p>

<dl>
  <dt>|</dt>
  <dd>Boolean OR or set UNION</dd>
  <dt>&</dt>
  <dd>Boolean AND or set INTERSECT</dd>
  <dt>!</dt>
  <dd>Boolean NOT or set EXCEPT</dd>
  <dt>:</dt>
  <dd>Boolean eXclusive OR or set UNION - INTERSECT</dd>
</dl>

<h3>Field selectors</h3>

<dl>
  <dt>country</dt>
  <dt>state</dt>
  <dt>region</dt>
  <dt>town</dt>
  <dt>city</dt>
  <dt>location</dt>
  <dd>country/state/region/town</dd>
  <dt>age</dt>
  <dt>date</dt>
  <dt>gender</dt>
  <dt>sex</dt>
</dl>

'''
