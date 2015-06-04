
# This is utility for common tasks

from msaf.models import *

def get_ladder(ladder_name):

    ladder_spec = EK.get( EK._id(ladder_name) )

    return json.loads( ladder_spec.data.decode('UTF-8') )





