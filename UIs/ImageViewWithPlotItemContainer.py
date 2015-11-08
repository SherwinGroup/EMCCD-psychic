__author__ = 'Home'

import pyqtgraph as pg
import numpy as np


class ImageViewWithPlotItemContainer(pg.ImageView):
    """
    I make all my uis with Qt Designer.
    I want an image view class so I can use the time-trace
    portion to display multiple ccd images as a funciton of
    "time". But it's practically necessary to have the pixel
    number labeled to compare them. THis requires passing
    the view to the imageView as a plotItem at construction

    Qt Designer doesn't allow that functionality. One option
    is to change the pyqtgrpah source so that the default
    view is a plotitem, not a viewbox, but that's super
    cumbersome to carry through to every single computer

    The alternative is to subclass it so I can force
    the view kwarg to be a plotitem, as I want

    """
    def __init__(self, *args, **kwargs):
        kwargs["view"] = pg.PlotItem()
        super(ImageViewWithPlotItemContainer, self).__init__(*args, **kwargs)
    def setImage(self, img,  *args, **kwargs):
        # Screw you, Luke. For some fucking reason,
        # you decided that a 3D image which as a second dimension
        # length of <=4, that there's supposed to be some fucking flipping
        # of the axes so one of them is a color pallete? Why the
        # fuck would you do that?
        # if you dont pass the axes for it here so that
        # he can't randomly fucking redefine them on me.
        # Fucking ass.
        axes = kwargs.get("axes", None)
        if axes is None:
            kwargs["axes"] = {'t': 0, 'x': 1, 'y': 2, 'c': None}

        resize = kwargs.get("tranpose", True)
        if resize:
            if img.ndim == 3:
                img = np.transpose(img, (0, 2, 1))
            elif img.ndim == 2:
                img = img.T
                # need to set it to 3 axes to deal with
                # setting the axes as above

                img = img[None,:,:]

        super(ImageViewWithPlotItemContainer, self).setImage(img, *args, **kwargs)