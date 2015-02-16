

# The class should be general. If we want
# to have different classes for different experiments
# (HSG, PL, Abs ...)
# If we do want to have different things for live processing,
# I think that'll have to be the next version of the UI
# to actually be able to handle all of that
class Psuedo(object):

    # I'd call an object once a scan is finished.
    # Assume the data is a np.array() with the appropriate shape
    # *args (or *kwargs?) can be all of the scan parameters for that scan
    #   Since I haven't done anything for this, you can pick names/conventions
    #   and I'll make sure the right stuff gets passed to it
    #
    # Maybe we need a different flag for background vs. signal?
    def __init__(self, data = None, *args):
        self. data = data

    # Would be good to be able to add/subract two of them,
    # at the very least for signal/background purposes.
    # Would be useful for future implementation if we do a series
    # and want to add them up live.
    def __add__(self, other):
        pass

    def __sub__(self, other):
        pass

    # Maybe adding the ability to divide by an integer so that
    # we can normalize by FEL pulses or something else
    def __div__(self, other):
        pass

    # This one will need to be considered. Either there can be settings
    # in the gui to specify parameters used for doing the correction, or
    # we can try to agree on what we think would the most applicable settings
    # We can also maybe add a flag in the GUI to see if this processing wants to be done
    # live or not
    #
    # Also, I wouldn't return a value, just have it set an internal data set
    def cosmicRayRemoval(self):
        pass

    # Sum along the axes, as expected.
    # I'd also just toss in the append_wavelength function
    # because I don't really know when we'd ever need to integrate without
    # also wanting to convert pixels to wavelength
    def integrate(self):
        pass

    # Do we want to save clean data or dirty? Or both?
    # Or, again, should they be flags in the UI?
    # We could do live processing just for live viewing, but leave it
    # to post-processing to redo it for more control
    #
    # We could maybe look into compression schemes
    # File name/directory can get passed back during __init__.
    def save(self):
        pass