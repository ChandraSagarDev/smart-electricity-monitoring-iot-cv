from datetime import datetime

# This class contains all logic for calculating electricity bills based on consumption, phase, and tariff rules.
class ElectricityBillCalculator:
    def __init__(self, is_single_phase=True, is_bpl=False, connected_load=None):
        self.is_single_phase = is_single_phase
        self.is_bpl = is_bpl
        self.connected_load = connected_load  # in watts
        
        # For single-phase (old structure)
        self.fixed_charges = {
            'single': {
                50: 40, 100: 65, 150: 85, 200: 120, 250: 130,
                300: 150, 350: 175, 400: 200, 500: 230, 501: 260
            },
            'three': {
                50: 100, 100: 140, 150: 170, 200: 180, 250: 200,
                300: 205, 350: 210, 400: 210, 500: 235, 501: 260
            }
        }
        
        # Telescopic and non-telescopic rates used for single-phase calculations.
        self.telescopic_rates = {
            40: 1.50,   
            50: 3.25,
            100: 4.05,
            150: 5.10,
            200: 6.95,
            250: 8.20
        }
        
        self.non_telescopic_rates = {
            300: 6.40,
            350: 7.25,
            400: 7.60,
            500: 7.90,
            501: 8.80
        }
        
        # ToD rates multipliers (if applicable)
        self.tod_rates = {
            'normal': 1.0,    # 06:00-18:00
            'peak': 1.2,      # 18:00-22:00
            'off_peak': 0.9   # 22:00-06:00
        }
    
    def get_fixed_charge(self, units):
        """Get fixed charge based on consumption and phase type (for single phase)."""
        if self.is_bpl and units <= 40:
            return 0
            
        charges = self.fixed_charges['single' if self.is_single_phase else 'three']
        for limit in sorted(charges.keys()):
            if units <= limit:
                return charges[limit]
        return charges[501]  # Above 500 units

    def calculate_telescopic_bill(self, units):
        """Calculate telescopic bill for consumption ≤250 units (used for single phase)."""
        bill = 0
        remaining_units = units
        prev_slab = 0
        
        for limit, rate in sorted(self.telescopic_rates.items()):
            if remaining_units <= 0:
                break
            slab_units = min(remaining_units, limit - prev_slab)
            bill += slab_units * rate
            remaining_units -= slab_units
            prev_slab = limit
            
        return bill

    def calculate_non_telescopic_bill(self, units):
        """Calculate non-telescopic bill for consumption >250 units (used for single phase)."""
        for limit, rate in sorted(self.non_telescopic_rates.items()):
            if units <= limit:
                return units * rate
        return units * self.non_telescopic_rates[501]

    def calculate_lt1_bill(self, units, current_time):
        """Calculate tariff for LT1 domestic three phase users based on KSEB slabs."""
        # Assumed fixed charge for LT1 domestic three phase
        fixed_charge = 240  
        energy_charge = 0
        remaining = units
        # Define slabs: (slab capacity, rate)
        slabs = [
            (50, 4.31),
            (50, 5.47),
            (50, 6.71),
            (50, 7.95),
            (50, 8.91)
        ]
        for slab_units, rate in slabs:
            if remaining > 0:
                consumption = min(remaining, slab_units)
                energy_charge += consumption * rate
                remaining -= consumption
            else:
                break
        # Any consumption above 250 units
        if remaining > 0:
            energy_charge += remaining * 9.63
        
        # For LT1, typically no separate ToD charge applies.
        tod_charge = 0
        # Electricity duty (assumed 10%)
        duty = energy_charge * 0.10
        total = fixed_charge + energy_charge + tod_charge + duty
        
        return {
            'total': round(total, 2),
            'fixed_charge': round(fixed_charge, 2),
            'energy_charge': round(energy_charge, 2),
            'tod_charge': tod_charge,
            'duty': round(duty, 2),
            'subsidy': 0,
            'final': round(total, 2)
        }
    
    def calculate_tod_charges(self, units, current_hour):
        """Calculate ToD charges if applicable (for single phase)."""
        if units <= 500:
            return 0
        base_rate = self.non_telescopic_rates[501]
        if 6 <= current_hour < 18:
            return units * base_rate * self.tod_rates['normal']
        elif 18 <= current_hour < 22:
            return units * base_rate * self.tod_rates['peak']
        else:
            return units * base_rate * self.tod_rates['off_peak']

    def calculate_bill(self, units, current_time=None):
        """Calculate total electricity bill based on consumption."""
        if current_time is None:
            current_time = datetime.now()
        
        # For single-phase use the original methods.
        if self.is_single_phase:
            # NPG consumer exemption
            if self.connected_load and self.connected_load <= 500 and units <= 30:
                return {
                    'total': 0,
                    'fixed_charge': 0,
                    'energy_charge': 0,
                    'tod_charge': 0,
                    'duty': 0,
                    'subsidy': 0,
                    'final': 0
                }
            fixed_charge = self.get_fixed_charge(units)
            if units <= 250:
                energy_charge = self.calculate_telescopic_bill(units)
            else:
                energy_charge = self.calculate_non_telescopic_bill(units)
            tod_charge = self.calculate_tod_charges(units, current_time.hour)
            duty = energy_charge * 0.10
            subsidy = 0
            if self.is_single_phase and units <= 120:
                subsidy = 20
            total = fixed_charge + energy_charge + tod_charge + duty
            final = total - subsidy
            return {
                'total': round(total, 2),
                'fixed_charge': round(fixed_charge, 2),
                'energy_charge': round(energy_charge, 2),
                'tod_charge': round(tod_charge, 2),
                'duty': round(duty, 2),
                'subsidy': round(subsidy, 2),
                'final': round(final, 2)
            }
        else:
            # For three-phase, use LT1 tariff calculations.
            return self.calculate_lt1_bill(units, current_time)
