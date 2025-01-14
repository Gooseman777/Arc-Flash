import math

## Idea/ Steps for Arc Flash
    # Determine arcing current 
        # 600 - 15000V
            # Use equations 1, 16, 17, 18
        # 208 - 600V
            # Use equations 1 and 25
    # Determine arc duration using 6.9
    # Determine incident energy
        # Determine enclosure correction factor
        # 600 - 15000V use equations 3, 4, 5 to find intermediatevalues and 19, 20, 21 to find the final values
        # 208-600V use equation 6 and guidance from 4.10
        # Consult 6.10 
    # Determine arc flash boundary 
        # Determine correction factor per 4.8
        # 600 - 15000V use equations 7, 8, 9, then use 22, 23, 24 and 4.9 to find the final arc-flash boundary
        # 208 - 600V use equation 10 and 4.10
    # Reiterate using 4.5

# Define coefficients for different systems
    # fix values but the concept works
coefficientsIARC = {
    'VCB_600V':     {'k1': -0.04287,  'k2': 1.035, 'k3': -0.083,  'k4': 0,          'k5': 0,          'k6': -4.783E-09, 'k7': 1.962E-06, 'k8': -0.000229, 'k9': 0.003141, 'k10': 1.092},
    'VCB_2700V':    {'k1': 0.0065,    'k2': 1.001, 'k3': -0.024,  'k4': -1.557E-12, 'k5': 4.556E-10,  'k6': -4.186E-08, 'k7': 8.346E-07, 'k8': 5.482E-05, 'k9': -0.003191, 'k10': 0.9729},
    'VCB_14300V':   {'k1': 0.005795,  'k2': 1.015, 'k3': -0.011,  'k4': -1.557E-12, 'k5': 4.556E-10,  'k6': -4.186E-08, 'k7': 8.346E-07, 'k8': 5.482E-05, 'k9': -0.003191, 'k10': 0.9729},
    'VCBB_600V' :   {'k1': -0.017432, 'k2': 0.98,  'k3': -0.05,   'k4': 0,          'k5': 0,          'k6': -5.767E-09, 'k7': 2.524E-06, 'k8': -0.00034,  'k9': 0.01187, 'k10': 1.013},
    'VCBB_2700V' :  {'k1': 0.002823,  'k2': 0.995, 'k3': -0.0125, 'k4': 0,          'k5': -9.204E-11, 'k6': 2.901E-08,  'k7': -3.262E-06,'k8': 0.0001569, 'k9': -0.004003, 'k10': 0.9825},
    'VCBB_14300V' : {'k1': 0.014827,  'k2': 1.01,  'k3': -0.01,   'k4': 0,          'k5': -9.204E-11, 'k6': 2.901E-08,  'k7': -3.262E-06,'k8': 0.0001569, 'k9': -0.004003, 'k10': 0.9825},
    'HCB_600V':     {'k1': 0.054922,  'k2': 0.988, 'k3': -0.11,   'k4': 0,          'k5': 0,          'k6': -5.382E-09, 'k7': 2.316E-06, 'k8': -0.000302, 'k9': 0.0091,  'k10': 0.9725},
    'HCB_2700V':    {'k1': 0.001011,  'k2': 1.003, 'k3': -0.0249, 'k4': 0,          'k5': 0,          'k6': 4.859E-10,  'k7': -1.814E-07,'k8': -9.128E-06,'k9': -0.0007, 'k10': 0.9881},
    'HCB_14300V':   {'k1': 0.008693,  'k2': 0.999, 'k3': -0.02,   'k4': 0,          'k5': -5.043E-11, 'k6': 2.233E-08,  'k7': -3.046E-06,'k8': 0.000116,  'k9': -0.001145,  'k10': 0.9839},
    'VOA_600V':     {'k1': 0.043785,  'k2': 1.04,  'k3': -0.18,   'k4': 0,          'k5': 0,          'k6': -4.783E-08, 'k7': 1.962E-06, 'k8': -0.000229, 'k9': 0.003141, 'k10': 1.092},
    'VOA_2700V':    {'k1': -0.02395,  'k2': 1.006, 'k3': -0.0188, 'k4': -1.557E-12, 'k5': 4.556E-10,  'k6': -4.186E-08, 'k7': 8.346E-07, 'k8': 5.482E-05, 'k9': -0.003191, 'k10': 0.9729},
    'VOA_14300V':   {'k1': 0.005371,  'k2': 1.0102,'k3': -0.029,  'k4': -1.557E-12, 'k5': 4.556E-10,  'k6': -4.186E-08, 'k7': 8.346E-07, 'k8': 5.482E-05, 'k9': -0.003191, 'k10': 0.9729},
    'HOA_600V':     {'k1': 0.111147,  'k2': 1.008, 'k3': -0.24,   'k4': 0,          'k5': 0,          'k6': -3.895E-09, 'k7': 1.641E-06, 'k8': -0.000197, 'k9': 0.002615, 'k10': 1.1},
    'HOA_2700V':    {'k1': 0.000435,  'k2': 1.006, 'k3': -0.038,  'k4': 0,          'k5': 0,          'k6': 7.859E-10,  'k7': -1.914E-07,'k8': -9.128E-06,'k9': -0.0007, 'k10': 0.9981},
    'HOA_14300V':   {'k1': 0.000904,  'k2': 0.999, 'k3': -0.02,   'k4': 0,          'k5': 0,          'k6': 7.859E-10,  'k7': -1.914E-07,'k8': -9.128E-06,'k9': -0.0007, 'k10': 0.9981}
}


coefficientsEncCF = {
    'Typical_VCB':  {'b1': -0.000302,  'b2': 0.03441,  'b3': 0.4325},
    'Typical_VCBB': {'b1': -0.0002976, 'b2': 0.032,    'b3': 0.479},
    'Typical_HCB':  {'b1': -0.0001923, 'b2': 0.01935,  'b3': 0.6899},
    'Shallow_VCB':  {'b1': 0.002222,   'b2': -0.02556, 'b3': 0.6222},
    'Shallow_VCBB': {'b1': -0.002778,  'b2': 0.1194,   'b3': -0.2778},
    'Shallow_HCB':  {'b1': -0.0005556, 'b2': 0.03722,  'b3': 0.4778}
}

coefficientsInterIE = {
    'VCB_600':    {'k1': 0.753364, 'k2': 0.566, 'k3': 1.752636,  'k4': 0,          'k5': 0,          'k6': -4.783E-09, 'k7': 0.000001962, 'k8': -0.000229,  'k9': 0.003141,  'k10': 1.092,  'k11': 0,     'k12': -1.598, 'k13': 0.957 },
    'VCBB_600':   {'k1': 3.068459, 'k2': 0.26,  'k3': -0.098107, 'k4': 0,          'k5': 0,          'k6': -5.767E-09, 'k7': 0.000002524, 'k8': -0.00034,   'k9': 0.01187,   'k10': 1.013,  'k11': -0.06, 'k12': -1.809, 'k13': 1.19 },
    'HCB_600':    {'k1': 4.073745, 'k2': 0.344, 'k3': -0.370259, 'k4': 0,          'k5': 0,          'k6': -5.382E-09, 'k7': 0.000002316, 'k8': -0.000302,  'k9': 0.0091,    'k10': 0.9725, 'k11': 0,     'k12': -2.03,  'k13': 1.036 },
    'VOA_600':    {'k1': 0.679294, 'k2': 0.746, 'k3': 1.222636,  'k4': 0,          'k5': 0,          'k6': -4.783E-09, 'k7': 0.000001962, 'k8': -0.000229,  'k9': 0.003141,  'k10': 1.092,  'k11': 0,     'k12': -1.598, 'k13': 0.997 },
    'HOA_600':    {'k1': 3.470417, 'k2': 0.465, 'k3': -0.261863, 'k4': 0,          'k5': 0,          'k6': -3.895E-09, 'k7': 0.000001641, 'k8': -0.000197,  'k9': 0.002615,  'k10': 1.1,    'k11': 0,     'k12': -1.99,  'k13': 1.04 },
    'VCB_2700':   {'k1': 2.40021,  'k2': 0.165, 'k3': 0.354202,  'k4': -1.557E-12, 'k5': 4.556E-10,  'k6': -4.186E-08, 'k7': 8.346E-07,   'k8': 5.482E-05,  'k9': -0.003191, 'k10': 0.9729, 'k11': 0,     'k12': -1.569, 'k13': 0.9778 },
    'VCBB_2700':  {'k1': 3.870592, 'k2': 0.185, 'k3': -0.736618, 'k4': 0,          'k5': -9.204E-11, 'k6': 2.901E-08,  'k7': -3.262E-06,  'k8': 0.0001569,  'k9': -0.004003, 'k10': 0.9825, 'k11': 0,     'k12': -1.742, 'k13': 1.09 },
    'HCB_2700':   {'k1': 3.486391, 'k2': 0.177, 'k3': -0.193101, 'k4': 0,          'k5': 0,          'k6': 4.859E-10,  'k7': -1.814E-07,  'k8': -9.128E-06, 'k9': -0.0007,   'k10': 0.9881, 'k11': 0.027, 'k12': -1.723, 'k13': 1.055 },
    'VOA_2700':   {'k1': 3.880724, 'k2': 0.105, 'k3': -1.906033, 'k4': -1.557E-12, 'k5': 4.556E-10,  'k6': -4.186E-08, 'k7': 8.346E-07,   'k8': 5.482E-05,  'k9': -0.003191, 'k10': 0.9729, 'k11': 0,     'k12': -1.515, 'k13': 1.115 },
    'HOA_2700':   {'k1': 3.616266, 'k2': 0.149, 'k3': -0.761561, 'k4': 0,          'k5': 0,          'k6': 7.859E-10,  'k7': -1.914E-07,  'k8': -9.128E-06, 'k9': -0.0007,   'k10': 0.9981, 'k11': 0,     'k12': -1.639, 'k13': 1.078 },
    'VCB_14300':  {'k1': 3.825917, 'k2': 0.11,  'k3': -0.999749, 'k4': -1.557E-12, 'k5': 4.556E-10,  'k6': -4.186E-08, 'k7': 8.346E-07,   'k8': 5.482E-05,  'k9': -0.003191, 'k10': 0.9729, 'k11': 0,     'k12': -1.568, 'k13': 0.99 },
    'VCBB_14300': {'k1': 3.644309, 'k2': 0.215, 'k3': -0.585522, 'k4': 0,          'k5': -9.204E-11, 'k6': 2.901E-08,  'k7': -3.262E-06,  'k8': 0.0001569,  'k9': -0.004003, 'k10': 0.9825, 'k11': 0,     'k12': -1.677, 'k13': 1.06 },
    'HCB_14300':  {'k1': 3.044516, 'k2': 0.125, 'k3': 0.245106,  'k4': 0,          'k5': -5.043E-11, 'k6': 2.233E-08,  'k7': -3.046E-06,  'k8': 0.000116,   'k9': -0.001145, 'k10': 0.9839, 'k11': 0,     'k12': -1.655, 'k13': 1.084 },
    'VOA_14300':  {'k1': 3.405454, 'k2': 0.12,  'k3': -0.93245,  'k4': -1.557E-12, 'k5': 4.556E-08,  'k6': -4.186E-08, 'k7': 8.346E-07,   'k8': 5.482E-05,  'k9': -0.003191, 'k10': 0.9729, 'k11': 0,     'k12': -1.534, 'k13': 0.979 },
    'HOA_14300':  {'k1': 2.04049,  'k2': 0.177, 'k3': 1.005092,  'k4': 0,          'k5': 0,          'k6': 7.859E-10,  'k7': 7.859E-10,   'k8': -9.128E-06, 'k9': -0.0007,   'k10': 0.9981, 'k11': -0.05, 'k12': -1.633, 'k13': 1.151 }
}

# Equation 1
def calc_intermediate_arcing_current(I_bf, G, electrodeConfig, voltage):
    system_type = f"{electrodeConfig}_{voltage}V"
    
    # Get the coefficients for the selected system type
    coeffs = coefficientsIARC.get(system_type)
    
    if not coeffs:
        raise ValueError(f"Invalid system type: {system_type}")
    
    # Unpack the coefficients
    k1 = coeffs['k1']
    k2 = coeffs['k2']
    k3 = coeffs['k3']
    k4 = coeffs['k4']
    k5 = coeffs['k5']
    k6 = coeffs['k6']
    k7 = coeffs['k7']
    k8 = coeffs['k8']
    k9 = coeffs['k9']
    k10 = coeffs['k10']
    
    log_term = k1 + k2 * math.log10(I_bf) + k3 * math.log10(G)
    
    # Calculate the polynomial term
    polynomial_term = (
        k4 * I_bf**6 + 
        k5 * I_bf**5 + 
        k6 * I_bf**4 + 
        k7 * I_bf**3 + 
        k8 * I_bf**2 + 
        k9 * I_bf + 
        k10
    )
    
    # Calculate the intermediate arcing current
    I_arc_Voc = 10**log_term * polynomial_term
    
    return I_arc_Voc


# Equation 16 17 18 
def calc_final_arc_current(voltage):
    
    I_arc_1 = ((I_arc_2700 - I_arc_600) / 2) * (voltage - 2.7) + I_arc_2700
    I_arc_2 = ((I_arc_14300 - I_arc_2700) / 11.6) * (voltage - 14.3) + I_arc_14300
    I_arc_3 = ((I_arc_1 * (2.7 - voltage)) / 2.1) + ((I_arc_2 * (voltage - 0.6)) / 2.1)
    
    if voltage > 0.6 and voltage < 2.7:
        return I_arc_3
    else:
        return I_arc_2

# Equation 25
def calc_final_arc_current_lv(voltage, I_bf, G, electrodeConfig):
    I_arc_600 = calc_intermediate_arcing_current(I_bf, G, electrodeConfig, 600)
    
    I_arc_small = 1 / math.sqrt(((0.6 / voltage)**2) * (1 / (I_arc_600 ** 2) - ((0.6 ** 2 - voltage ** 2) / (0.6 ** 2 * I_bf ** 2))))
    return I_arc_small

# Enclosure size correction factor (Equations 13, 14, 15)
def calc_enclosure_size(height, width, depth, voltage):
    # Determine enclosure type
    if voltage < .600 and height < 508 and width < 508 and depth <= 203.2: #mm
        enclosureType = 'Shallow'
        return enclosureType
    else:
        enclosureType = 'Typical'
        return enclosureType

def calculate_new_dimensions(electrodeConfig, width, height, depth, voltage):
    # Constants
    WIDTH_THRESHOLD_1 = 508
    WIDTH_THRESHOLD_2 = 660.4
    WIDTH_THRESHOLD_3 = 1244.6
    HEIGHT_THRESHOLD_1 = WIDTH_THRESHOLD_1  # Same as width
    HEIGHT_THRESHOLD_2 = WIDTH_THRESHOLD_2  # Same as width
    HEIGHT_THRESHOLD_3 = WIDTH_THRESHOLD_3  # Same as width
    
    enclosureType = calc_enclosure_size(height, width, depth, voltage)
    # Assign constants A and B based on electrodeConfig
    if electrodeConfig == 'VCB':
        A, B = 4, 20
    elif electrodeConfig == 'VCBB':
        A, B = 10, 24
    elif electrodeConfig == 'HCB':
        A, B = 10, 22
    else:
        raise ValueError("Invalid electrode configuration")

    def get_new_dimension(dimension, threshold1, threshold2, threshold3, enclosureType, is_width=True):
        if dimension < threshold1:
            return 20 if enclosureType == 'Typical' else 0.03937 * dimension
        elif threshold1 <= dimension <= threshold2:
            return 0.03937 * dimension
        elif threshold2 < dimension <= threshold3:
            return equiv_width(voltage, A, B, dimension) if is_width else 0.03937 * dimension
        else:
            return equiv_width(voltage, A, B, threshold3) if is_width else 49

    # VCB, VCBB, and HCB cases all share the same logic with different A and B constants
    new_width = get_new_dimension(width, WIDTH_THRESHOLD_1, WIDTH_THRESHOLD_2, WIDTH_THRESHOLD_3, enclosureType, is_width=True)
    new_height = get_new_dimension(height, HEIGHT_THRESHOLD_1, HEIGHT_THRESHOLD_2, HEIGHT_THRESHOLD_3, enclosureType, is_width=False)

    # Equivalent enclosure size
    EES = (new_height + new_width) / 2
    
    system_type = f"{enclosureType}_{electrodeConfig}"
    
    # Get the coefficients for the selected system type
    coeffs = coefficientsEncCF.get(system_type)
    
    if not coeffs:
        raise ValueError(f"Invalid system type: {system_type}")
    
    # Unpack the coefficients
    b1 = coeffs['b1']
    b2 = coeffs['b2']
    b3 = coeffs['b3']
    if enclosureType == 'Typical':
        CF = b1 * (EES ** 2) + b2 * EES +b3
        return CF
    else:
        CF = 1 / (b1 * (EES ** 2) + b2 * EES +b3)
        return CF
    
def equiv_width(voltage, A, B, dimension):
    # Formula for equivalent width/height
    return (660.4 + (dimension - 660.4) * ((voltage + A) / B)) * (1 / 25.4)

#Equations 3, 4, 5, 6
def incident_energy(voltage, CF, T, G, D, I_bf, electrodeConfig):    

    # Incident Energy
    system_type = f"{electrodeConfig}_{600}"
    # Get the coefficients for the selected system type
    coeffs =coefficientsInterIE.get(system_type)
    
    k1 = coeffs['k1']
    k2 = coeffs['k2']
    k3 = coeffs['k3']
    k4 = coeffs['k4']
    k5 = coeffs['k5']
    k6 = coeffs['k6']
    k7 = coeffs['k7']
    k8 = coeffs['k8']
    k9 = coeffs['k9']
    k10 = coeffs['k10']
    k11 = coeffs['k11']
    k12 = coeffs['k12']
    k13 = coeffs['k13'] 
    E_600 = (12.552 / 50) * T * 10**(k1 + k2 * math.log10(G) + (k3 * I_arc_600) / 
        (k4 * I_bf**7 + k5 * I_bf**6 + k6 * I_bf**5 + k7 * I_bf**4 + k8 * I_bf**3 + k9 * I_bf**2 + k10 * I_bf) +
        k11 * math.log10(I_bf) + k12 * math.log10(D) + k13 * math.log10(I_arc_600) + math.log10(1 / CF))
    
    system_type = f"{electrodeConfig}_{2700}"
    # Get the coefficients for the selected system type
    coeffs =coefficientsInterIE.get(system_type)
    
    k1 = coeffs['k1']
    k2 = coeffs['k2']
    k3 = coeffs['k3']
    k4 = coeffs['k4']
    k5 = coeffs['k5']
    k6 = coeffs['k6']
    k7 = coeffs['k7']
    k8 = coeffs['k8']
    k9 = coeffs['k9']
    k10 = coeffs['k10']
    k11 = coeffs['k11']
    k12 = coeffs['k12']
    k13 = coeffs['k13'] 
    E_2700 = (12.552 / 50) * T * 10**(k1 + k2 * math.log10(G) + (k3 * I_arc_2700) / 
        (k4 * I_bf**7 + k5 * I_bf**6 + k6 * I_bf**5 + k7 * I_bf**4 + k8 * I_bf**3 + k9 * I_bf**2 + k10 * I_bf) +
        k11 * math.log10(I_bf) + k12 * math.log10(D) + k13 * math.log10(I_arc_2700) + math.log10(1 / CF))
    
    system_type = f"{electrodeConfig}_{14300}"
    # Get the coefficients for the selected system type
    coeffs =coefficientsInterIE.get(system_type)
    
    k1 = coeffs['k1']
    k2 = coeffs['k2']
    k3 = coeffs['k3']
    k4 = coeffs['k4']
    k5 = coeffs['k5']
    k6 = coeffs['k6']
    k7 = coeffs['k7']
    k8 = coeffs['k8']
    k9 = coeffs['k9']
    k10 = coeffs['k10']
    k11 = coeffs['k11']
    k12 = coeffs['k12']
    k13 = coeffs['k13'] 
    E_14300 = (12.552 / 50) * T * 10**(k1 + k2 * math.log10(G) + (k3 * I_arc_14300) / 
        (k4 * I_bf**7 + k5 * I_bf**6 + k6 * I_bf**5 + k7 * I_bf**4 + k8 * I_bf**3 + k9 * I_bf**2 + k10 * I_bf) +
        k11 * math.log10(I_bf) + k12 * math.log10(D) + k13 * math.log10(I_arc_14300) + math.log10(1 / CF))
    # Equation 6 so will be used differently
    if voltage <= .6:
        E_less600 = (12.552 / 50) * T * 10**(k1 + k2 * math.log10(G) + (k3 * I_arc_600) / 
            (k4 * I_bf**7 + k5 * I_bf**6 + k6 * I_bf**5 + k7 * I_bf**4 + k8 * I_bf**3 + k9 * I_bf**2 + k10 * I_bf) +
            k11 * math.log10(I_bf) + k12 * math.log10(D) + k13 * math.log10(I_arc_less600) + math.log10(1 / CF))
        print("Incident energy works")
        return E_less600
    #Calculates the total Incident Energy
    else:
        if voltage > 0.6 and voltage < 2.7:
            E1 = (E_2700 - E_600)/2.1 * (voltage -2.7) + E_2700
            return E1
        elif voltage > 2.7:
            E2 = (E_14300 - E_2700)/11.6 * (voltage - 14.3) + E_14300
            return E2
        else:
            E3 = (E1 * (2.7 - voltage))/2.1 + (E2 * (voltage -0.6))/2.1
            return E3 

def calculate_boundary(voltage, CF, T, G, I_bf, electrodeConfig):
    def constant(electrodeConfig, voltage):
        system_type = f"{electrodeConfig}_{voltage}"
        # Get the coefficients for the selected system type
        coeffs = coefficientsInterIE.get(system_type)

        if coeffs is None:
            raise ValueError(f"Coefficients for system type '{system_type}' not found in coefficientsInterIE")

        return [coeffs[f'k{i}'] for i in range(1, 14)]
    
    if voltage <= .6:
        # Equation 10
        # k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, _, k13 = constant(electrodeConfig, 600)
        system_type = f"{electrodeConfig}_{600}"
        # Get the coefficients for the selected system type
        coeffs =coefficientsInterIE.get(system_type)
    
        k1 = coeffs['k1']
        k2 = coeffs['k2']
        k3 = coeffs['k3']
        k4 = coeffs['k4']
        k5 = coeffs['k5']
        k6 = coeffs['k6']
        k7 = coeffs['k7']
        k8 = coeffs['k8']
        k9 = coeffs['k9']
        k10 = coeffs['k10']
        k11 = coeffs['k11']
        k12 = coeffs['k12']
        k13 = coeffs['k13']
        AFB_600Less = 10**(((k1 + k2*math.log10(G)) + (k3*I_arc_600)/(k4*(I_bf**7) + k5*(I_bf**6) + k6*(I_bf**5) + k7*(I_bf**4) +
                   k8*(I_bf**3) + k9*(I_bf**2) + k10*I_bf) + (k11*math.log10(I_bf) + k13*math.log10(I_arc_600) + 
                   math.log10(1/CF) - math.log10(20/T)))/(-k12))
        print(f"ARC Flash Works")
        return AFB_600Less
    else:
        # Equation 7
        # k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, _, k13 = constant(electrodeConfig, 600)
        system_type = f"{electrodeConfig}_{600}"
        # Get the coefficients for the selected system type
        coeffs =coefficientsInterIE.get(system_type)
    
        k1 = coeffs['k1']
        k2 = coeffs['k2']
        k3 = coeffs['k3']
        k4 = coeffs['k4']
        k5 = coeffs['k5']
        k6 = coeffs['k6']
        k7 = coeffs['k7']
        k8 = coeffs['k8']
        k9 = coeffs['k9']
        k10 = coeffs['k10']
        k11 = coeffs['k11']
        k12 = coeffs['k12']
        k13 = coeffs['k13']
        AFB_600 = 10**(((k1 + k2*math.log10(G)) + (k3*I_arc_600)/(k4*(I_bf**7) + k5*(I_bf**6) + k6*(I_bf**5) + k7*(I_bf**4) +
                   k8*(I_bf**3) + k9*(I_bf**2) + k10*I_bf) + (k11*math.log10(I_bf) + k13*math.log10(I_arc_600) + 
                   math.log10(1/CF) - math.log10(20/T)))/(-k12))
        # Equation 8
        # k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, _, k13 = constant(electrodeConfig, 2700)
        system_type = f"{electrodeConfig}_{2700}"
        # Get the coefficients for the selected system type
        coeffs =coefficientsInterIE.get(system_type)
    
        k1 = coeffs['k1']
        k2 = coeffs['k2']
        k3 = coeffs['k3']
        k4 = coeffs['k4']
        k5 = coeffs['k5']
        k6 = coeffs['k6']
        k7 = coeffs['k7']
        k8 = coeffs['k8']
        k9 = coeffs['k9']
        k10 = coeffs['k10']
        k11 = coeffs['k11']
        k12 = coeffs['k12']
        k13 = coeffs['k13']
        AFB_2700 = 10**(((k1 + k2*math.log10(G)) + (k3*I_arc_2700)/(k4*(I_bf**7) + k5*(I_bf**6) + k6*(I_bf**5) + k7*(I_bf**4) +
                   k8*(I_bf**3) + k9*(I_bf**2) + k10*I_bf) + (k11*math.log10(I_bf) + k13*math.log10(I_arc_2700) + 
                   math.log10(1/CF) - math.log10(20/T)))/(-k12))
        # Equation 9
        # k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, _, k13 = constant(electrodeConfig, 14300)
        system_type = f"{electrodeConfig}_{14300}"
        # Get the coefficients for the selected system type
        coeffs =coefficientsInterIE.get(system_type)
    
        k1 = coeffs['k1']
        k2 = coeffs['k2']
        k3 = coeffs['k3']
        k4 = coeffs['k4']
        k5 = coeffs['k5']
        k6 = coeffs['k6']
        k7 = coeffs['k7']
        k8 = coeffs['k8']
        k9 = coeffs['k9']
        k10 = coeffs['k10']
        k11 = coeffs['k11']
        k12 = coeffs['k12']
        k13 = coeffs['k13']
        AFB_14300 = 10**(((k1 + k2*math.log10(G)) + (k3*I_arc_14300)/(k4*(I_bf**7) + k5*(I_bf**6) + k6*(I_bf**5) + k7*(I_bf**4) +
                   k8*(I_bf**3) + k9*(I_bf**2) + k10*I_bf) + (k11*math.log10(I_bf) + k13*math.log10(I_arc_14300) + 
                   math.log10(1/CF) - math.log10(20/T)))/(-k12))
        
        AFB1 = (AFB_2700 - AFB_600)/2.1 * (voltage - 2.7) + AFB_2700
        AFB2 = (AFB_14300 - AFB_2700)/11.6 * (voltage - 14.3) + AFB_14300
        AFB3 = (AFB1 * (2.7 - voltage))/2.1 + (AFB2 * (voltage - 0.6))/2.1

        if voltage > 2.7:
            return AFB2
        else:
            return AFB3    
     

# Initialize count and global variables
count = 1
I_arc_600 = I_arc_2700 = I_arc_14300 = I_arc_less600 = None

def values(count):
    if count == 1:
        # High Voltage
        I_bf = 15  # Example bolted fault current (kA)
        G = 104  # Example gap distance (mm)
        electrodeConfig = 'VCB'  # Example system type
        voltage = 4.16  # (kV)
        T = 197  # (ms)
        D = 914.4  # Working Distance, in mm
        width = 762  # (mm)
        height = 1143  # (mm)
        depth = 204  # Only relevant for certain systems
    else:
        # Low Voltage
        I_bf = 45  # Example bolted fault current (kA)
        G = 32  # Example gap distance (mm)
        electrodeConfig = 'VCB'  # Example system type
        voltage = 0.48  # (kV)
        T = 61.3  # (ms)
        D = 609.6  # Working Distance, in mm
        width = 610  # (mm)
        height = 610  # (mm)
        depth = 254  # Only relevant for certain systems
    
    # Calculate arcing currents
    I_arc_600 = calc_intermediate_arcing_current(I_bf, G, electrodeConfig, 600)
    I_arc_2700 = calc_intermediate_arcing_current(I_bf, G, electrodeConfig, 2700)
    I_arc_14300 = calc_intermediate_arcing_current(I_bf, G, electrodeConfig, 14300)
    I_arc_less600 = calc_final_arc_current_lv(voltage, I_bf, G, electrodeConfig)
    
    # Return all necessary data
    return {
        "I_bf": I_bf,
        "G": G,
        "electrodeConfig": electrodeConfig,
        "voltage": voltage,
        "T": T,
        "D": D,
        "width": width,
        "height": height,
        "depth": depth,
        "I_arc_600": I_arc_600,
        "I_arc_2700": I_arc_2700,
        "I_arc_14300": I_arc_14300,
        "I_arc_less600": I_arc_less600
    }

# Loop through voltage scenarios
while count < 3:
    data = values(count)
    I_bf = data["I_bf"]
    G = data["G"]
    electrodeConfig = data["electrodeConfig"]
    voltage = data["voltage"]
    T = data["T"]
    D = data["D"]
    width = data["width"]
    height = data["height"]
    depth = data["depth"]
    
    # Update global variables
    I_arc_600 = data["I_arc_600"]
    I_arc_2700 = data["I_arc_2700"]
    I_arc_14300 = data["I_arc_14300"]
    I_arc_less600 = data["I_arc_less600"]
    
    if 0.6 < voltage <= 15:
        print(f"High Voltage")
        I_arc_Final = calc_final_arc_current(voltage) 
        print(f"Final arcing current: {I_arc_Final} kA")
        CF = calculate_new_dimensions(electrodeConfig, width, height, depth, voltage)
        IE = incident_energy(voltage, CF, T, G, D, I_bf, electrodeConfig)
        print(f"Incident Energy: {IE} cal/cm2")
        Boundary = calculate_boundary(voltage, CF, T, G, I_bf, electrodeConfig)
        print(f"Arc Flash Boundary: {Boundary} mm")
    elif 0.208 <= voltage <= 0.6:
        print(f"Low Voltage")
        I_arc_Final = calc_final_arc_current_lv(voltage, I_bf, G, electrodeConfig)  
        print(f"Final arcing current: {I_arc_Final} kA")
        CF = calculate_new_dimensions(electrodeConfig, width, height, depth, voltage)
        IE = incident_energy(voltage, CF, T, G, D, I_bf, electrodeConfig)
        print(f"Incident Energy: {IE} cal/cm2")
        Boundary = calculate_boundary(voltage, CF, T, G, I_bf, electrodeConfig)
        print(f"Arc Flash Boundary: {Boundary} mm")
    
    count += 1  # Increment count to move to the next scenario


    
# What do we do for voltage less than 208??    