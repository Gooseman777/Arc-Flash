import math
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
import pandas as pd
from openpyxl import Workbook  # For advanced Excel formatting

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

# ==== DATABASE CLASS START ====
class ArcFlashDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('arc_flash_components.db')
        self.create_tables()
        
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS component_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_id INTEGER,
                x REAL,
                y REAL,
                FOREIGN KEY (component_id) REFERENCES components(id)
            )
        ''')
        self.conn.commit()
        
    def get_components(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM components")
        return [row[0] for row in cursor.fetchall()]
        
    def add_component(self, name):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO components (name) VALUES (?)", (name,))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
            
    def add_data_point(self, component_name, x, y):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM components WHERE name = ?", (component_name,))
        component_id = cursor.fetchone()
        if component_id:
            cursor.execute("INSERT INTO component_data (component_id, x, y) VALUES (?, ?, ?)",
                          (component_id[0], x, y))
            self.conn.commit()
            return True
        return False
        
    def delete_component(self, name):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM components WHERE name = ?", (name,))
        self.conn.commit()
# ==== DATABASE CLASS END ====

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

coefficientsIARCMIN = {
    'VCB':  {'k1': 0,          'k2': -0.0000014269, 'k3': 0.000083137, 'k4': -0.0019382, 'k5': 0.022366, 'k6': -0.12645, 'k7': 0.30226},
    'VCBB': {'k1': 1.138E-06,  'k2': -6.0287E-05,   'k3': 0.0012758,   'k4': -0.013778,  'k5': 0.080217, 'k6': -0.24066, 'k7': 0.33524},
    'HCB':  {'k1': 0,          'k2': -3.097E-06,    'k3': 0.00016405,  'k4': -0.0033609, 'k5': 0.033308, 'k6': -0.16182, 'k7': 0.34627},
    'VOA':  {'k1': 9.5606E-07, 'k2': -5.1543E-05,   'k3': 0.0011161,   'k4': -0.01242,   'k5': 0.075125, 'k6': -0.23584, 'k7': 0.33696},
    'HOA':  {'k1': 0,          'k2': -3.1555E-06,   'k3': 0.0001682,   'k4': -0.0034607, 'k5': 0.034124, 'k6': -0.1599,  'k7': 0.34629}
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

# Global Variables
I_arc_600 = I_arc_2700 = I_arc_14300 = I_arc_less600 = 0


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

# Equation 2
def calc_minimum_arc_current(electrodeConfig, voltage, current):
    system_type = f"{electrodeConfig}"
    
    # Get the coefficients for the selected system type
    coeffs = coefficientsIARCMIN.get(system_type)
    
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
    
    # Calculate correction factor (CF) using voltage in kV
    CF = k1 * voltage**6 + k2 * voltage**5 + k3 * voltage**4 + k4 * voltage**3 + k5 * voltage**2 + k6 * voltage + k7
    print(CF)
    adjusted_current = current * (1 - 0.5 * CF)
    return adjusted_current

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
def read_scenarios_from_excel(file_path):
    df = pd.read_excel(file_path)
    scenarios = df.to_dict('records')
    return scenarios
def compute_var_cf(electrodeConfig, voltage_kV):
    """Compute variation correction factor for a given voltage"""
    coeffs = coefficientsIARCMIN.get(electrodeConfig)
    if not coeffs:
        raise ValueError(f"Invalid electrode config: {electrodeConfig}")
    return (
        coeffs['k1'] * voltage_kV**6 +
        coeffs['k2'] * voltage_kV**5 +
        coeffs['k3'] * voltage_kV**4 +
        coeffs['k4'] * voltage_kV**3 +
        coeffs['k5'] * voltage_kV**2 +
        coeffs['k6'] * voltage_kV +
        coeffs['k7']
    )

def calculate_boundary_with_currents(voltage, CF, T, G, I_bf, electrodeConfig, I_arc_600_val, I_arc_2700_val, I_arc_14300_val):
    """Calculate boundary without modifying global variables"""
    global I_arc_600, I_arc_2700, I_arc_14300
    # Store original values
    original_600 = I_arc_600
    original_2700 = I_arc_2700
    original_14300 = I_arc_14300
    # Set temporary values
    I_arc_600 = I_arc_600_val
    I_arc_2700 = I_arc_2700_val
    I_arc_14300 = I_arc_14300_val
    try:
        return calculate_boundary(voltage, CF, T, G, I_bf, electrodeConfig)
    finally:
        # Restore originals
        I_arc_600 = original_600
        I_arc_2700 = original_2700
        I_arc_14300 = original_14300

def process_scenarios(file_path):
    global I_arc_600, I_arc_2700, I_arc_14300, I_arc_less600
    scenarios = read_scenarios_from_excel(file_path)
    results = []

    for index, params in enumerate(scenarios):
        result = [
            f"\n{'='*40}",
            f"Scenario {index+1}",
            f"{'-'*40}"
        ]
        
        # Extract parameters
        try:
            I_bf = params["I_bf"]
            G = params["G"]
            electrodeConfig = params["electrodeConfig"]
            voltage = params["voltage"]  # in kV
            orig_T = params["T"]
            D = params["D"]
            width = params["width"]
            height = params["height"]
            depth = params["depth"]

            # Calculate intermediate values
            result.append("\nIntermediate Arcing Currents:")
            I_arc_600_int = calc_intermediate_arcing_current(I_bf, G, electrodeConfig, 600)
            I_arc_2700_int = calc_intermediate_arcing_current(I_bf, G, electrodeConfig, 2700)
            I_arc_14300_int = calc_intermediate_arcing_current(I_bf, G, electrodeConfig, 14300)
            
            result.append(f"600V System: {I_arc_600_int:.2f} kA")
            result.append(f"2700V System: {I_arc_2700_int:.2f} kA")
            result.append(f"14300V System: {I_arc_14300_int:.2f} kA")

            # Calculate correction factor once using scenario's voltage
            VarC_f = compute_var_cf(electrodeConfig, voltage)
            adjusted_factor = 1 - 0.5 * VarC_f
            I_arc_600 = I_arc_600_int * adjusted_factor
            I_arc_2700 = I_arc_2700_int * adjusted_factor
            I_arc_14300 = I_arc_14300_int * adjusted_factor

            result.append("\nMinimum Arcing Currents (Adjusted):")
            result.append(f"600V System: {I_arc_600:.2f} kA")
            result.append(f"2700V System: {I_arc_2700:.2f} kA")
            result.append(f"14300V System: {I_arc_14300:.2f} kA")

            # Compute enclosure correction factor
            CF = calculate_new_dimensions(electrodeConfig, width, height, depth, voltage)
            
            # Calculate original boundary with intermediate currents
            original_boundary = calculate_boundary_with_currents(
                voltage, CF, orig_T, G, I_bf, electrodeConfig,
                I_arc_600_int, I_arc_2700_int, I_arc_14300_int
            )
            result.append(f"\nOriginal Arc Flash Boundary: {original_boundary:.2f} mm")

            # Final calculations with adjusted currents
            if 0.6 < voltage <= 15:
                I_arc_Final = calc_final_arc_current(voltage)
                result.append(f"\nFinal Arcing Current: {I_arc_Final:.2f} kA")
                
                IE = incident_energy(voltage, CF, orig_T, G, D, I_bf, electrodeConfig)
                adjusted_boundary = calculate_boundary(voltage, CF, orig_T, G, I_bf, electrodeConfig)
                
                result.append(f"Incident Energy: {IE:.2f} cal/cm²")
                result.append(f"Adjusted Arc Flash Boundary: {adjusted_boundary:.2f} mm")

                # ====== NEW POPUP CODE STARTS HERE ======
                # Create popup for new T value
                popup = tk.Toplevel(root)
                popup.title("New T Value Input")
                popup.geometry("300x150")
                
                # Display final arcing current in popup
                tk.Label(popup, 
                         text=f"Final Arcing Current: {I_arc_Final:.2f} kA\nEnter new T (ms):",
                         wraplength=250).pack(pady=10)
                
                new_T_entry = tk.Entry(popup)
                new_T_entry.pack(pady=5)
                
                confirmed = [False]  # Track if valid input was received
                
                def on_submit():
                    try:
                        new_T = float(new_T_entry.get())
                        if new_T <= 0: raise ValueError
                        # Recalculate with new T
                        IE_new = incident_energy(voltage, CF, new_T, G, D, I_bf, electrodeConfig)
                        boundary_new = calculate_boundary(voltage, CF, new_T, G, I_bf, electrodeConfig)
                        
                        result.extend([
                            f"\n=== With Custom T ===",
                            f"New T Value: {new_T} ms",
                            f"Updated Incident Energy: {IE_new:.2f} cal/cm²",
                            f"Updated Boundary: {boundary_new:.2f} mm"
                        ])
                        confirmed[0] = True
                        popup.destroy()
                    except ValueError:
                        messagebox.showerror("Error", "Invalid T value. Must be positive number.")
                
                tk.Button(popup, text="Submit", command=on_submit).pack(pady=5)
                
                # Make popup modal
                popup.grab_set()
                root.wait_window(popup)
                
                if not confirmed[0]:
                    result.append("\nNo valid T value entered - using original results")
                # ====== NEW POPUP CODE ENDS HERE ======

        except Exception as e:
            result.append(f"\nError in calculations: {str(e)}")

        results.extend(result)

    # Write output file
    folder_path = os.path.dirname(file_path)
    output_file_path = os.path.join(folder_path, "detailed_results.txt")
    
    with open(output_file_path, 'w') as f:
        f.write("\n".join(results))

    print(f"Detailed results written to {output_file_path}")
    return output_file_path

def compute_var_cf(electrodeConfig, voltage_kV):
    coeffs = coefficientsIARCMIN.get(electrodeConfig)
    if not coeffs:
        raise ValueError(f"Invalid electrode configuration: {electrodeConfig}")
    k1 = coeffs['k1']
    k2 = coeffs['k2']
    k3 = coeffs['k3']
    k4 = coeffs['k4']
    k5 = coeffs['k5']
    k6 = coeffs['k6']
    k7 = coeffs['k7']
    VarC_f = (k1 * voltage_kV**6 + k2 * voltage_kV**5 + k3 * voltage_kV**4 +
              k4 * voltage_kV**3 + k5 * voltage_kV**2 + k6 * voltage_kV + k7)
    return VarC_f

def calculate_boundary_with_currents(voltage, CF, T, G, I_bf, electrodeConfig, I_arc_600_val, I_arc_2700_val, I_arc_14300_val):
    global I_arc_600, I_arc_2700, I_arc_14300
    original_600 = I_arc_600
    original_2700 = I_arc_2700
    original_14300 = I_arc_14300

    I_arc_600 = I_arc_600_val
    I_arc_2700 = I_arc_2700_val
    I_arc_14300 = I_arc_14300_val

    try:
        boundary = calculate_boundary(voltage, CF, T, G, I_bf, electrodeConfig)
    finally:
        I_arc_600 = original_600
        I_arc_2700 = original_2700
        I_arc_14300 = original_14300

    return boundary

def validate_inputs(**kwargs):
    """
    Validate inputs to ensure they are within a valid mathematical domain.
    Returns True if all inputs are valid; otherwise raises a ValueError.
    """
    for key, value in kwargs.items():
        if value is None:
            raise ValueError(f"{key} is None.")
        if isinstance(value, (int, float)) and value <= 0:
            raise ValueError(f"{key} must be positive. Got {value}.")
    return True



def plot_valid_values(results, output_file_path="incident_energy_vs_ibf.png"):
    """
    Plot all valid (I_bf, incident energy) pairs on a graph, highlight the maximum value,
    local maxima, and save the graph as an image.
    
    Parameters:
    - results: A list of dictionaries containing 'I_bf' and 'IE' for valid scenarios.
    - output_file_path: Path where the image will be saved (default is 'incident_energy_vs_ibf.png').
    """
    if not results:
        print("No valid data to plot.")
        return

    # Extract valid values
    I_bf_values = [result['I_bf'] for result in results]
    IE_values = [result['IE'] for result in results]

    # Find the maximum value
    max_index = IE_values.index(max(IE_values))
    max_I_bf = I_bf_values[max_index]
    max_IE = IE_values[max_index]

    # Find local maxima
    peaks, _ = find_peaks(IE_values)
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(I_bf_values, IE_values, label='Incident Energy vs I_bf', marker='o')
    
    # Highlight the global maximum
    plt.scatter([max_I_bf], [max_IE], color='red', label=f'Max: I_bf={max_I_bf}, IE={max_IE:.2f}', s=100)

    # Highlight local maxima
    plt.scatter([I_bf_values[i] for i in peaks], [IE_values[i] for i in peaks], color='green', label='Local Maxima', zorder=5)

    # Set title and labels
    plt.title("Incident Energy vs I_bf")
    plt.xlabel("Bolted Fault Current (I_bf) [kA]")
    plt.ylabel("Incident Energy (IE) [cal/cm²]")
    plt.legend()
    plt.grid()

    # Save the plot as an image file
    plt.savefig(output_file_path, dpi=300)  # Save with 300 DPI for good quality
    plt.close()  # Close the plot to avoid display in non-interactive environments

    print(f"Graph saved as {output_file_path}")


def process_scenarios_with_range(file_path):
    """
    Process scenarios and plot valid values of I_bf vs Incident Energy.
    Generate a detailed and clean output report.
    """
    global I_arc_600, I_arc_2700, I_arc_14300, I_arc_less600
    scenarios = read_scenarios_from_excel(file_path)
    results = []  # Collect results to write to the output file
    valid_results = []  # Collect valid results for plotting

    for scenario_index, params in enumerate(scenarios):
        results.append(f"--- Scenario {scenario_index + 1} ---")
        try:
            # Extract and validate static parameters
            G = params.get("G")
            electrodeConfig = params.get("electrodeConfig")
            voltage = params.get("voltage")
            T = params.get("T")
            D = params.get("D")
            width = params.get("width")
            height = params.get("height")
            depth = params.get("depth")

            
            validate_inputs(
                G=G, voltage=voltage, T=T, D=D, width=width, height=height, depth=depth
            )

            results.append(f"Voltage: {voltage} kV | Electrode Config: {electrodeConfig}")
            results.append(f"{'I_bf (kA)':<12}                {'IE (cal/cm²)':<15}")

            # Iterate I_bf from 9999 to 1, decrementing by 0.1
            I_bf_values = np.arange(9999, 0, -0.1)  # Using numpy's arange to create decimal steps
            for I_bf in I_bf_values:
                try:
                    validate_inputs(I_bf=I_bf)

                    # Calculate arcing currents
                    I_arc_600 = calc_intermediate_arcing_current(I_bf, G, electrodeConfig, 600)
                    I_arc_2700 = calc_intermediate_arcing_current(I_bf, G, electrodeConfig, 2700)
                    I_arc_14300 = calc_intermediate_arcing_current(I_bf, G, electrodeConfig, 14300)

                    if 0.6 < voltage <= 15:
                        I_arc_Final = calc_final_arc_current(voltage)
                        CF = calculate_new_dimensions(electrodeConfig, width, height, depth, voltage)
                        IE = incident_energy(voltage, CF, T, G, D, I_bf, electrodeConfig)

                    elif 0.208 <= voltage <= 0.6:
                        I_arc_Final = calc_final_arc_current_lv(voltage, I_bf, G, electrodeConfig)
                        CF = calculate_new_dimensions(electrodeConfig, width, height, depth, voltage)
                        IE = incident_energy(voltage, CF, T, G, D, I_bf, electrodeConfig)

                    else:
                        continue

                    # Append valid result for plotting and reporting
                    valid_results.append({'I_bf': I_bf, 'IE': IE})
                    results.append(f"{I_bf:<12}           {IE:<15}")

                except ValueError as ve:
                    continue  # Skip invalid I_bf values

        except ValueError as ve:
            results.append(f"Scenario skipped due to invalid parameters: {ve}")

    # Write results to a text file in the same folder as the input file
    global folder_path, output_file_path
    folder_path = os.path.dirname(file_path)
    output_file_path = os.path.join(folder_path, "iteration_outputs.txt")

    with open(output_file_path, 'w') as output_file:
        output_file.write("\n".join(results))

    print(f"Results written to {output_file_path}")

    # Plot valid results
    plot_valid_values(valid_results)

    return output_file_path

def process_nathaniel_test(file_path, variable, min_val=None, max_val=None, step=None, configs=None):
    """
    Process Nathaniel Test:
    - variable: The variable to change (e.g., "I_bf", "G", "electrodeConfig").
    - min_val, max_val, step: For numerical variables.
    - configs: For electrodeConfig (comma-separated list of configurations).
    """
    scenarios = read_scenarios_from_excel(file_path)
    output_data = []
    
    if not scenarios:
        raise ValueError("No scenarios found in the Excel file.")
    
    # Use the first scenario as the base
    base_scenario = scenarios[0]
    
    # Generate values for the selected variable
    if variable == "electrodeConfig":
        if not configs:
            raise ValueError("Please provide configurations for electrodeConfig.")
        var_values = [config.strip() for config in configs.split(",")]
    else:
        if min_val is None or max_val is None or step is None:
            raise ValueError("Please provide min, max, and step for numerical variables.")
        var_values = np.arange(float(min_val), float(max_val) + float(step), float(step))
    
    # Process each value
    for value in var_values:
        scenario = base_scenario.copy()
        scenario[variable] = value
        
        # Extract variables for calculations
        I_bf = scenario.get("I_bf")
        G = scenario.get("G")
        electrodeConfig = scenario.get("electrodeConfig")
        voltage = scenario.get("voltage")
        T = scenario.get("T")
        D = scenario.get("D")
        width = scenario.get("width")
        height = scenario.get("height")
        depth = scenario.get("depth")
        
        # Calculate enclosure correction factor
        CF = calculate_new_dimensions(electrodeConfig, width, height, depth, voltage)
        
        # Calculate intermediate arcing currents
        I_arc_600 = calc_intermediate_arcing_current(I_bf, G, electrodeConfig, 600)
        I_arc_2700 = calc_intermediate_arcing_current(I_bf, G, electrodeConfig, 2700)
        I_arc_14300 = calc_intermediate_arcing_current(I_bf, G, electrodeConfig, 14300)
        
        # Calculate final arcing current
        if 0.6 < voltage <= 15:
            I_arc_Final = calc_final_arc_current(voltage)
        elif 0.208 <= voltage <= 0.6:
            I_arc_Final = calc_final_arc_current_lv(voltage, I_bf, G, electrodeConfig)
        else:
            raise ValueError("Voltage out of range.")
        
        # Calculate Incident Energy
        IE = incident_energy(voltage, CF, T, G, D, I_bf, electrodeConfig)
        
        # Calculate Arc Flash Boundary
        AFB = calculate_boundary(voltage, CF, T, G, I_bf, electrodeConfig)
        
        # Add results to output
        output_row = {
            "Scenario #": 1,  # Use a single scenario number
            "Variable Changed": f"{variable} = {value}",
            **scenario,  # Include all constant variables
            "Incident Energy": IE,  # Calculated value
            "Arc Flash Boundary": AFB  # Calculated value
        }
        output_data.append(output_row)
    
    # Save to Excel
    df_output = pd.DataFrame(output_data)
    output_path = os.path.join(os.path.dirname(file_path), "nathaniel_test_results.xlsx")
    df_output.to_excel(output_path, index=False)
    return output_path

def browse_file():
    filepath = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])  # Changed to Excel
    if filepath:  # If a file is selected
        file_path_entry.delete(0, tk.END)  # Clear previous text
        file_path_entry.insert(0, filepath)  # Insert the selected file path into the entry field

def submit():
    file_path = file_path_entry.get()
    processing_mode = processing_mode_var.get()

    if file_path:
        output_file_path = None  # Initialize the variable
        try:
            if processing_mode == "Standard Processing":
                output_file_path = process_scenarios(file_path)
            elif processing_mode == "Range Processing":
                output_file_path = process_scenarios_with_range(file_path)
            elif processing_mode == "Nathaniel Test":
                # Get Nathaniel Test inputs
                variable = variable_var.get()
                min_val = min_entry.get()
                max_val = max_entry.get()
                step = step_entry.get()
                configs = config_entry.get()
                
                # Call Nathaniel Test function
                output_file_path = process_nathaniel_test(
                    file_path, variable, min_val, max_val, step, configs
                )
            
            if output_file_path:  # Check if output_file_path was assigned
                result_label.config(text=f"Processing complete. Results saved to:\n{output_file_path}")
            else:
                result_label.config(text="Error: No output file path was generated.")
        except Exception as e:
            result_label.config(text=f"Error: {e}")
    else:
        result_label.config(text="Please select a file.")
# Create the main window
root = tk.Tk()
# ==== DATABASE INIT START ====
db = ArcFlashDatabase()
# ==== DATABASE INIT END ====
root.title("File Path Submission")

# Create widgets
label = tk.Label(root, text="Enter or browse to a text file:")
label.pack(pady=5)

file_path_entry = tk.Entry(root, width=40)
file_path_entry.pack(pady=5)

# ==== COMPONENT UI START ====
mgmt_frame = tk.LabelFrame(root, text="Component Database")
mgmt_frame.pack(pady=10, fill=tk.X)

# Component Dropdown
tk.Label(mgmt_frame, text="Component:").grid(row=0, column=0, padx=5)
component_var = tk.StringVar()
component_dropdown = ttk.Combobox(mgmt_frame, textvariable=component_var)
component_dropdown.grid(row=0, column=1, padx=5)

# New Component Entry
tk.Label(mgmt_frame, text="New:").grid(row=1, column=0, padx=5)
new_component_entry = tk.Entry(mgmt_frame)
new_component_entry.grid(row=1, column=1, padx=5)

# Data Entries
tk.Label(mgmt_frame, text="X (Amps in KA):").grid(row=2, column=0, padx=5)
x_entry = tk.Entry(mgmt_frame, width=10)
x_entry.grid(row=2, column=1, padx=5)

tk.Label(mgmt_frame, text="Y (Seconds):").grid(row=2, column=2, padx=5)
y_entry = tk.Entry(mgmt_frame, width=10)
y_entry.grid(row=2, column=3, padx=5)

# Control Buttons
tk.Button(mgmt_frame, text="Add Component", command=lambda: add_component(db, new_component_entry, component_dropdown, component_var)).grid(row=3, column=0, columnspan=2, pady=5)
tk.Button(mgmt_frame, text="Add Data", command=lambda: add_data(db, component_var, x_entry, y_entry)).grid(row=3, column=2, columnspan=2, pady=5)
tk.Button(mgmt_frame, text="Delete", command=lambda: delete_component(db, component_var, component_dropdown)).grid(row=4, column=0, columnspan=4, pady=5)

# Initial component list update
def update_component_list():
    components = db.get_components()
    component_dropdown['values'] = components
    if components:
        component_var.set(components[0])

update_component_list()
# ==== COMPONENT UI END ====

browse_button = tk.Button(root, text="Browse", command=browse_file)
browse_button.pack(pady=5)

# Dropdown menu for selecting processing mode
processing_mode_var = tk.StringVar(value="Standard Processing")
processing_mode_label = tk.Label(root, text="Select Processing Mode:")
processing_mode_label.pack(pady=5)

processing_mode_dropdown = tk.OptionMenu(
    root, 
    processing_mode_var, 
    "Standard Processing", 
    "Range Processing",
    "Nathaniel Test" # new mode
)
processing_mode_dropdown.pack(pady=5)

submit_button = tk.Button(root, text="Submit", command=submit)
submit_button.pack(pady=5)

# Nathaniel Test Inputs
nathaniel_frame = tk.LabelFrame(root, text="Nathaniel Test Parameters")
nathaniel_frame.pack(pady=10, fill=tk.X)

# Variable to Change Dropdown
tk.Label(nathaniel_frame, text="Variable to Change:").grid(row=0, column=0, padx=5)
variable_var = tk.StringVar(value="I_bf")  # Default to I_bf
variable_dropdown = ttk.Combobox(nathaniel_frame, textvariable=variable_var)
variable_dropdown['values'] = ["I_bf", "G", "voltage", "T", "D", "width", "height", "depth", "electrodeConfig"]
variable_dropdown.grid(row=0, column=1, padx=5)

# Min, Max, Step Inputs (for numerical variables)
tk.Label(nathaniel_frame, text="Min:").grid(row=1, column=0, padx=5)
min_entry = tk.Entry(nathaniel_frame, width=10)
min_entry.grid(row=1, column=1, padx=5)

tk.Label(nathaniel_frame, text="Max:").grid(row=1, column=2, padx=5)
max_entry = tk.Entry(nathaniel_frame, width=10)
max_entry.grid(row=1, column=3, padx=5)

tk.Label(nathaniel_frame, text="Step:").grid(row=1, column=4, padx=5)
step_entry = tk.Entry(nathaniel_frame, width=10)
step_entry.grid(row=1, column=5, padx=5)

# Electrode Config Input (for electrodeConfig variable)
tk.Label(nathaniel_frame, text="Configurations:").grid(row=2, column=0, padx=5)
config_entry = tk.Entry(nathaniel_frame, width=30)
config_entry.grid(row=2, column=1, columnspan=5, padx=5)

result_label = tk.Label(root, text="", justify=tk.LEFT)
result_label.pack(pady=10)

# ==== DATABASE FUNCTIONS START ====
def add_component(db, entry, dropdown, var):
    new_name = entry.get()
    if new_name:
        if db.add_component(new_name):
            entry.delete(0, tk.END)
            components = db.get_components()
            dropdown['values'] = components
            var.set(new_name)
            tk.messagebox.showinfo("Success", "Component added!")
        else:
            tk.messagebox.showerror("Error", "Component already exists!")

def add_data(db, var, x_entry, y_entry):
    component = var.get()
    try:
        x = float(x_entry.get())
        y = float(y_entry.get())
        if db.add_data_point(component, x, y):
            x_entry.delete(0, tk.END)
            y_entry.delete(0, tk.END)
            tk.messagebox.showinfo("Success", "Data added!")
        else:
            tk.messagebox.showerror("Error", "Component not found!")
    except ValueError:
        tk.messagebox.showerror("Error", "Invalid X/Y values")

def delete_component(db, var, dropdown):
    component = var.get()
    if component and tk.messagebox.askyesno("Confirm", f"Delete {component}?"):
        db.delete_component(component)
        components = db.get_components()
        dropdown['values'] = components
        if components:
            var.set(components[0])
        else:
            var.set('')
        tk.messagebox.showinfo("Deleted", f"{component} removed")
# ==== DATABASE FUNCTIONS END ====

# Run the GUI
root.mainloop()