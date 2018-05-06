# -*- coding: utf-8 -*-
# Main module for dust_attenuation


import numpy as np
import astropy.units as u

from astropy.io import ascii
from astropy.table import Table
from astropy.modeling.tabular import tabular_model

from .base_classes import BaseAtttauVModel, _test_valid_x_range



__all__ = ['WG00']

# validity range in microns
x_range_WG00 = [0.1, 3.0001]

class WG00(BaseAtttauVModel):
    """ 
    Attenuation curve of Witt & Gordon (2000)

    Parameters
    ----------
    tau_v: float
        optical depth in V band

    Raises
    ------
    InputParameterError
       Input Av values outside of defined range

    Notes
    -----
    From Witt & Gordon (2000, ApJ, Volume 528, pp. 799-816)

    Example:

    .. plot::
        :include-source:

        import numpy as np
        import matplotlib.pyplot as plt
        import astropy.units as u

        from dust_attenuation.dust_attenuation import WG00

        fig, ax = plt.subplots()

        # generate the curves and plot them
        x = np.arange(0.33,10.0,0.1)/u.micron

        tau_Vs = [0.25,0.4,1.1,17.0,46.0]
        for tau_V in tau_vs:
           att_model = WG00(tau_V=tau_V)
           ax.plot(x,att_model(x),label=r'$\tau_V$ = %.2f mag' % (tau_Av))

        ax.set_xlabel('$x$ [$\mu m^{-1}$]')
        ax.set_ylabel('$\tau(x)$ [mag]')

        ax.legend(loc='best')
        plt.show()


    """
    tau_V_range = [0.25, 50.0]
    x_range = x_range_WG00

    
    def get_model(self, geometry='dusty', dust_type='mw', dust_distribution='clumpy'):
        """ 
        Load the attenuation curves for a given geometry, dust type and
        dust distribution.

        Parameters
        ----------
        geometry: string
           'shell', 'cloudy' or 'dusty' 

        dust_type: string
           'mw' or 'smc'

        dust_distribution: string
           'homogeneous' or 'clumpy'

        Returns
        -------
        taux: np array (float)
            tau(x) attenuation curves for all optical depth [mag]

        """
        
        # Ensure strings are lower cases
        geometry = geometry.lower()
        dust_type = dust_type.lower()
        dust_distribution = dust_distribution.lower()

        if geometry == 'shell':
            filename = '../dust_attenuation/data/WG00/shell.txt' 
        elif geometry == 'dusty':
            filename = '../dust_attenuation/data/WG00/dusty.txt' 
        elif geometry == 'cloudy':
            filename = '../dust_attenuation/data/WG00/cloudy.txt' 
        
        data=ascii.read(filename,header_start=0)

        if dust_type == 'mw': 
            start = 0
        elif dust_type == 'smc':
            start = 25

        if dust_distribution == 'clumpy':
            column_name = 'tau_att_c'
        elif dust_distribution == 'homogeneous':
            column_name = 'tau_att_h'
    
        data_list = []
        len_data = len(data['lambda'])
        # number of lines between 2 models
        steps = 25

        counter = start
        while counter < len_data:
            data_list.append(np.array(data[column_name][counter:counter+steps]))
            counter += int(2*steps)
            
        # Convert to np.array and take transpose to have (wvl, tau_V)
        data_table = np.array(data_list).T

        # wavelength grid. It is the same for all the models
        wvl = np.array(data['lambda'][0:25])

        # Grid for the optical depth
        tau_V = np.array([0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 
                          4.0, 4.5, 5.0, 5.5, 6.0, 7.0, 8.0, 9.0, 10.0, 
                          15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0 ])

        # Create a 2D tabular model
        tab = tabular_model(2, name='Tabular_WG00')

        # Values corresponding to the x and y grid points
        gridpoints = (wvl, tau_V)

        self.model = tab(gridpoints, lookup_table=data_table, name='2D_table_WG00', bounds_error=False, fill_value=None, method='linear')

        #return model
    
    
    def evaluate(self, in_x, tau_V):
        """
        WG00 function

        Parameters
        ----------
        in_x: float
           expects either x in units of wavelengths or frequency
           or assumes wavelengths in wavenumbers [1/micron]

           internally wavenumbers are used

        Returns
        -------
        taux: np array (float)
            tau(x) attenuation curve [mag]

        Raises
        ------
        ValueError
           Input x values outside of defined range
        """
        # convert to wavenumbers (1/micron) if x input in units
        # otherwise, assume x in appropriate wavenumber units
        with u.add_enabled_equivalencies(u.spectral()):
            x_quant = u.Quantity(in_x, u.micron, dtype=np.float64)

        # strip the quantity to avoid needing to add units to all the
        #    polynomical coefficients
        x = x_quant.value

        # check that the wavenumbers are within the defined range
        _test_valid_x_range(x, x_range_WG00, 'WG00')

        # setup the ax vectors
        n_x = len(x)
        axEbv = np.zeros(n_x)

        xinterp = 1e4 * in_x 
        yinterp = tau_V * np.ones(n_x)
       
        taux = self.model(xinterp, yinterp) 
        return taux

