import pytest
import pandas as pd
import numpy as np
from qos_engine import calculate_qos_index

def test_qos_calculation_accuracy():
    """Verifică dacă formula QoS respectă ponderile (60% Pase, 40% Dueluri)."""
    test_data = pd.DataFrame([{
        'Node_ID': 1, 'Node_Name': 'Test', 'Network_Segment': 'TeamA',
        'Time_Minute': 10, 'Pass_Attempt': 10, 'Pass_Successful': 10,
        'Duel_Attempt': 10, 'Duel_Won': 5
    }])
    
    # Calcul manual: (100% pase * 0.6) + (50% dueluri * 0.4) = 60 + 20 = 80
    result = calculate_qos_index(test_data)
    assert result.iloc[0]['QoS_Index'] == 80.0

def test_zero_division_safety():
    """Verifică dacă sistemul crapă când un jucător nu are nicio acțiune (pachete 0)."""
    zero_data = pd.DataFrame([{
        'Node_ID': 2, 'Node_Name': 'IdleNode', 'Network_Segment': 'TeamA',
        'Time_Minute': 5, 'Pass_Attempt': 0, 'Pass_Successful': 0,
        'Duel_Attempt': 0, 'Duel_Won': 0
    }])
    
    result = calculate_qos_index(zero_data)
    assert result.iloc[0]['QoS_Index'] == 0.0 # Ar trebui să returneze 0, nu eroare